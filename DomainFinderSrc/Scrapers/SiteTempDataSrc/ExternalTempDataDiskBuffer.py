#from DomainFinderSrc.MiniServer.Common.DBInterface import ExternalSiteDB
from DomainFinderSrc.Utilities.FilePath import get_temp_db_dir
from DomainFinderSrc.Scrapers.SiteTempDataSrc.FileBufferInterface import FileBuffInterface, FileBuffDefaultState
from DomainFinderSrc.Utilities.Logging import *
from DomainFinderSrc.Utilities.FileIO import FileHandler
from DomainFinderSrc.Scrapers.SiteTempDataSrc.SiteTempDataSrcInterface import OnSiteLink
from DomainFinderSrc.Utilities.Serializable import Serializable
from DomainFinderSrc.Scrapers.SiteTempDataSrc.DBStruct import SiteTempExternalDatabase
from DomainFinderSrc.Utilities.TimeIt import timeit
from DomainFinderSrc.Scrapers.SiteTempDataSrc.DBStruct import TempDBInterface
from sqlite3 import OperationalError
io_log_timeout = 240


class ExternalTempInterface:
    def get_external_count_finished(self) -> int:
        """
        ExternalTempInterface, get the number of job done in ExternalTempDataDiskBuffer
        :return:
        """
        raise NotImplementedError

    def set_internal_count(self, count: int):
        """
        ExternalTempInterface, set the number of job done in ExternalTempDataDiskBuffer
        :param count:
        :return:
        """
        raise NotImplementedError


class ExternalTempDataDiskBuffer(FileBuffInterface):

    def __init__(self, file_name,  worker: ExternalTempInterface, stop_event: Event, buf_size=200,
                 dir_path="",  table_name="temp", convert_input=True, convert_output=True, terminate_callback=None):
        """

        :param file_name:
        :param worker:
        :param stop_event:
        :param buf_size:
        :param dir_path:
        :param table_name:
        :param convert_input:
        :param convert_output: convert output to OnSiteLink by default, else return raw tuple data.
        :return:
        """
        self._file_name = file_name
        if len(dir_path) > 0:
            self._file_dir = dir_path
        else:
            self._file_dir = get_temp_db_dir()
        self._file_path = self._file_dir + self._file_name
        PrintLogger.print("ExternalTempDataDiskBuffer create path in init: " + self._file_path)
        FileHandler.create_file_if_not_exist(self._file_path)
        self.stop_event = stop_event
        self._tab = table_name
        self._worker = worker
        self._get_lock = threading.RLock()
        self._put_lock = threading.RLock()
        self._convert_input = convert_input
        self._convert_output = convert_output
        FileBuffInterface.__init__(self, self._file_name, buf_size, power_save_mode=True,
                                   terminate_callback=terminate_callback)
        self.set_db_update_interval(10)

        self._is_reading = Event()
        self._need_to_vaccum = Event()
        self._total_record = self.count_all()
        # if 0 < self._total_record <= self._output_counter:
        #     self.set_continue_lock(False)

    def clear_cache(self):
        try:
            self.terminate()
            # restart
            self.reset()
            TempDBInterface.force_clear(self._file_name, self._file_dir)
            self.remove_power_save_db()
            #self.start_input_output_cycle()
            print("clear cache completed: "+self._file_name)
        except Exception as ex:
            ErrorLogger.log_error("ExternalTempDataDiskBuffer.clear_cache_and_restart()", ex, self._file_name)

    def get_db(self):
        temp = SiteTempExternalDatabase(self._file_name, self._file_dir)
        return temp

    def count_all(self):
        if self._need_to_vaccum.is_set():
            return self._total_record
        else:
            self._get_lock.acquire()
            self._is_reading.set()
            all_record = 0
            try:
                db = self.get_db()
                cur = db.cur.execute(u"SELECT COUNT(*) FROM TEMP;")
                result = cur.fetchone()
                db.close()
                all_record = result[0]
            except:
                all_record = self._total_record
            self._is_reading.clear()
            self._get_lock.release()
            return all_record

    def recovery_from_power_cut(self, data: Serializable):
        """
        power save mode method
        :param data:
        :return:
        """
        if isinstance(data, FileBuffDefaultState):
            self._worker.set_internal_count(data.progress)
            self._output_counter = data.progress
            self._total_record = data.all_data

    def get_state_for_power_save_mode(self):
        """
        power save mode method
        :return:
        """
        return FileBuffDefaultState(self._worker.get_external_count_finished(), self._total_record)

    def can_continue(self):
        return not self.stop_event.is_set()

    def get_task_done_count(self):
        return self._worker.get_external_count_finished()

    def set_vaccum(self):
        self._need_to_vaccum.set()

    @timeit("ExternalTempDataDiskBuffer.read()", io_log_timeout)
    def read(self, file=None) -> []:
        results = []
        if self._need_to_vaccum.is_set():
            pass
        else:
            self._get_lock.acquire()
            self._is_reading.set()
            if isinstance(file, SiteTempExternalDatabase):
                try:
                    output_cur = file.cur
                    results = output_cur.fetchmany(self._output_buff_size)
                except:
                    pass
            else:
                try:
                    query = u"SELECT * FROM TEMP ORDER BY ID LIMIT {0:d} " \
                            u"OFFSET {1:d};"
                        #u"OFFSET {1:d};".format(self.output_buff_size, self.temp_counter,)
                    output_db = self.get_db()
                    output_cur = output_db.cur.execute(query.format(self._output_buff_size, self._output_counter,))
                    results = output_cur.fetchall()

                    output_db.close()
                except Exception as ex:
                    msg = "output_cycling() read failed at " + self._file_path
                    ErrorLogger.log_error("ExternalTempDataDiskBuffer", ex, msg)
            # total_result = len(results)
            # if total_result == 0:
            #     if len(self._input_buff) == 0 and self.ref_obj.is_idle():
            #         self.set_continue_lock(False)
            # else:
            #     CsvLogger.log_to_file(self.ref, results) #####################################
            #     pass

            self._is_reading.clear()
            self._get_lock.release()
        return results

    @timeit("ExternalTempDataDiskBuffer.write()", io_log_timeout)
    def write(self, data: [], file=None) -> bool:
        append_OK = False
        if data is not None and len(data) > 0:
            is_exclusive_mode = False
            try:

                tempdb = self.get_db()
                if tempdb.should_vaccum_and_exclusive_access():
                    self._need_to_vaccum.set()

                if self._need_to_vaccum.is_set():
                    self._get_lock.acquire()
                    while self._is_reading.is_set() and self.can_continue():
                        time.sleep(0.1)
                    tempdb.enter_exclusive_mode()
                    is_exclusive_mode = True

                try:
                    if is_exclusive_mode:
                        PrintLogger.print("need to vacuum now!")
                        tempdb.vaccum_db()
                        while self.can_continue() and not tempdb.is_vaccum_finished():
                            time.sleep(0.1)
                    else:
                        if self._input_convert_tuple: #DataStruct.ScrapeDomainData
                            to_tuple = [(x.domain, x.code) for x in data]
                        else:
                            to_tuple = data
                        tempdb.cur.execute("BEGIN")
                        tempdb.cur.executemany("INSERT OR IGNORE INTO TEMP (LINK, RS_CODE) "
                                               "VALUES (?, ?);", to_tuple)
                        tempdb.db.commit()
                        append_OK = True
                except OperationalError as ex:
                    PrintLogger.print(ex)
                    msg = "ExternalTempDataDiskBuffer.write(), operation failed. " + self._file_path
                    ErrorLogger.log_error("SiteTempDataDiskWithBuffer", ex, msg)
                finally:
                    tempdb.close()
            except Exception as outer_ex:
                msg = "ExternalTempDataDiskBuffer,write() OperationalError, " + self._file_path
                ErrorLogger.log_error("SiteTempDataDiskWithBuffer", outer_ex, msg)
            finally:
                if is_exclusive_mode:
                    self._need_to_vaccum.clear()
                    self._get_lock.release()
        return append_OK

    def format_output(self, data):
        if self._convert_output:
            return OnSiteLink(data[0], data[1], link_type=OnSiteLink.TypeOutbound)
        else:
            return data

    def format_input(self, data):
        return data

    def update_total_in_file(self):
        return self.count_all()

    def use_same_connection_to_file(self):
        return False
