from DomainFinderSrc.Scrapers.SiteTempDataSrc.SiteTempDataDisk import *
from DomainFinderSrc.Scrapers.SiteTempDataSrc.SiteTempDataSrcInterface import OnSiteLink
from DomainFinderSrc.Utilities.Logging import *
from DomainFinderSrc.Utilities.TimeIt import timeit
from DomainFinderSrc.Scrapers.SiteTempDataSrc.FileBufferInterface import FileBuffInterface, FileBuffDefaultState
from DomainFinderSrc.Utilities.Serializable import Serializable

io_log_timeout = 240


class SiteTempDataDiskWithBuff(SiteTempDataDisk, FileBuffInterface):

    def __init__(self, *args, output_buff_size=2000, output_f=1000, **kwargs):
        SiteTempDataDisk.__init__(self, *args, **kwargs)
        FileBuffInterface.__init__(self, self.ref, output_buff_size=output_buff_size, output_f=output_f,
                                   power_save_mode=True)
        self._is_reading = Event()
        self._need_to_vaccum = Event()
        self.set_db_update_interval(5)
        self._total_record = SiteTempDataDisk.count_all(self)
        if 0 < self._total_record <= self._output_counter:
            self.set_continue_lock(False)

    def recovery_from_power_cut(self, data: Serializable):
        """
        if you have costumized state, pls implement your own Serializable and override this method
        :param data:
        :return:
        """
        if data is None:
            return
        if isinstance(data, FileBuffDefaultState):
            self._total_record = data.all_data
            print("self._output_counter value change in SiteTempDataDiskWithBuff.recovery_from_power_cut")
            self._output_counter = data.progress
            self.ref_obj.set_internal_page_progress_index(data.progress)
        else:
            pass

    def get_state_for_power_save_mode(self) ->Serializable:
        """
        if you have costumized state, pls implement your own Serializable and override this method
        :return:
        """
        return FileBuffDefaultState(self.ref_obj.get_internal_page_progress_index(), self._total_record)

    def additional_startup_procedures(self):
        super(SiteTempDataDiskWithBuff, self).start_input_output_cycle()

    def additional_finish_procedures(self):
        super(SiteTempDataDiskWithBuff, self).terminate()

    def append_many(self, new_data_list, convert_tuple=True):
        super(SiteTempDataDiskWithBuff, self).append_to_buffer(new_data_list, convert_tuple)

    def reset(self):
        self.reset_event.set()
        PrintLogger.print("in datasource going to reset")
        self.set_continue_lock(False)
        self._is_reading.clear()
        self._need_to_vaccum.clear()
        SiteTempDataDisk.reset(self)
        FileBuffInterface.reset(self)
        PrintLogger.print("in datasource reset completed")
        self.reset_event.clear()

    def __iter__(self):
        return FileBuffInterface.__iter__(self)

    def __next__(self):
        return FileBuffInterface.__next__(self)

    def set_progress(self, progress: int):
        SiteTempDataDisk.set_progress(self, progress)
        FileBuffInterface.set_progress(self, progress)
        #super(SiteTempDataDiskWithBuff, self).set_progress(progress)

    def set_continue_lock(self, can_contiune=True):
        SiteTempDataDisk.set_continue_lock(self, can_contiune)
        FileBuffInterface.set_continue_lock(self, can_contiune)
        #super(SiteTempDataDiskWithBuff, self).set_continue_lock(can_contiune)

    def can_continue(self):
        return FileBuffInterface.can_continue(self)

    def format_output(self, data):
        link, code, level, link_type, rowid = data
        return self.ref_obj, OnSiteLink(link, code, level, link_type)

    def count_all(self):
        if self._need_to_vaccum.is_set():
            return self.all_record
        else:
            self.get_lock.acquire()
            self._is_reading.set()
            all_record = SiteTempDataDisk.count_all(self)
            self._is_reading.clear()
            self.get_lock.release()
            return all_record

    @timeit("SiteTempDataDiskWithBuffer.read()", io_log_timeout)
    def read(self, file=None):
        results = []
        if self._need_to_vaccum.is_set():
            pass
        else:
            self.get_lock.acquire()
            self._is_reading.set()
            if isinstance(file, SiteTempDatabase):
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
                    output_db = SiteTempDatabase(self.ref)
                    output_cur = output_db.cur.execute(query.format(self._output_buff_size, self._output_counter,))
                    results = output_cur.fetchall()

                    output_db.close()
                except Exception as ex:
                    msg = "output_cycling() read failed at " + self.ref
                    ErrorLogger.log_error("SiteTempDataDiskWithBuffer", ex, msg)
            total_result = len(results)
            if total_result == 0:
                if len(self._input_buff) == 0 and self.ref_obj.is_idle():
                    #print("no data in buffer, and worker is idle, set stop now")
                    self.set_continue_lock(False)
            else:
                #CsvLogger.log_to_file(self.ref, results) #####################################
                pass
                #self.temp_counter += total_result
                #PrintLogger.print("fetched result count: " + str(total_result))
            self._is_reading.clear()
            self.get_lock.release()
        return results

    @timeit("SiteTempDataDiskWithBuffer.input_cycling().write()", io_log_timeout)
    def write(self, data: [], file=None) -> bool:
        append_OK = False
        if data is not None and len(data) > 0:
            is_exclusive_mode = False
            try:

                tempdb = SiteTempDatabase(self.ref)
                if tempdb.should_vaccum_and_exclusive_access():
                    self._need_to_vaccum.set()
                    self.get_lock.acquire()
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
                        if self._input_convert_tuple:
                            to_tuple = [(x.link, x.response_code, x.link_level, x.link_type) for x in data]
                        else:
                            to_tuple = data
                        tempdb.cur.execute("BEGIN")
                        tempdb.cur.executemany("INSERT OR IGNORE INTO TEMP (LINK, RS_CODE, LEV, L_TYPE) "
                                               "VALUES (?, ?, ?, ?);", to_tuple)
                        tempdb.db.commit()
                        append_OK = True
                except OperationalError as ex:
                    PrintLogger.print(ex)
                    msg = "SiteTempDataDiskWithBuffer.write(), operation failed. " + self.ref
                    ErrorLogger.log_error("SiteTempDataDiskWithBuffer", ex, msg)
                finally:
                    tempdb.close()
            except Exception as outer_ex:
                msg = "eSiteTempDataDiskWithBuffer,write() OperationalError, " + self.ref
                ErrorLogger.log_error("SiteTempDataDiskWithBuffer", outer_ex, msg)
            finally:
                if is_exclusive_mode:
                    self._need_to_vaccum.clear()
                    self.get_lock.release()
        return append_OK
        # return super(SiteTempDataDiskWithBuff, self).append_many(data, self._input_convert_tuple)

    def get_task_done_count(self):
        return self.ref_obj.get_internal_page_progress_index()

    def update_total_in_file(self):
        return self.count_all()

    def use_same_connection_to_file(self):
        return False

    # def open_file_object(self):
    #     try:
    #         query = u"SELECT * FROM TEMP ORDER BY rowid LIMIT -1 " \
    #                 u"OFFSET {0:d};"
    #         db = SiteTempDatabase(self.ref)
    #         db.cur.execute(query.format(self._output_counter,))
    #         return db
    #     except:
    #         return None
    #
    # def close_file_object(self, file):
    #     if isinstance(file, SiteTempDatabase):
    #         file.close()

