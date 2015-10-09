from multiprocessing import Queue, Event
import multiprocessing
from DomainFinderSrc.MiniServer.Common.SocketCommands import *
from DomainFinderSrc.MiniServer.Common.StreamSocket import StreamSocket
from DomainFinderSrc.MiniServer.Common.DBInterface import *
from DomainFinderSrc.Scrapers.SiteTempDataSrc.DataStruct import ScrapeDomainData
from DomainFinderSrc.MiniServer.Common.MiningTCPServer import MiningTCPServer
from DomainFinderSrc.UserAccountSettings.UserAccountDB import *
from DomainFinderSrc.Scrapers.MatrixFilterControl import FilterController, _FilterState
from DomainFinderSrc.Utilities.FilePath import *
from DomainFinderSrc.Utilities.MemoryControlProcess import MemoryControlPs
from DomainFinderSrc.Scrapers.LinkChecker import ResponseCode
from threading import RLock


def filtering_process(*args, **kwargs):
    filter_controller = FilterController(*args, **kwargs)
    filter_controller.begin_filtering()


class MiningController(threading.Thread):
    def __init__(self, target_server: Server, cmd: str=ServerCommand.Com_Start,
                 in_data: Serializable=None, out_data: []=None):
        threading.Thread.__init__(self)
        self.server = target_server
        self.cmd = cmd
        self.in_data = in_data
        self.out_data = out_data
        self.sock = StreamSocket()
        self.processor = CommandProcessor(self.sock.rfile, self.sock.wfile)

    def is_connection_ok(self):
        try:
            s = self.sock.get_connection()
            if isinstance(self.server.address, dict):
                self.server.address = Serializable.get_deserialized(self.server.address)
            s.connect((self.server.address.address, self.server.address.port))
            return True
        except Exception as e:
            print(e)
            return False

    def get_status(self):
        status_cmd = CommandStruct(cmd=ServerCommand.Com_Status)
        response = self.processor.check_response_ex(status_cmd)
        response_data = response[1].data
        if isinstance(response_data, dict):
            response_data = Serializable.get_deserialized(response_data)
        if not response[0]:
            raise ValueError("get status failed")
        elif response_data is not None and isinstance(response_data, ServerStatus):
            if isinstance(self.out_data, type([])):
                self.out_data.append(response_data)
            self.server.status = response_data

    def send_data(self):
        data_cmd = CommandStruct(cmd=ServerCommand.Com_Data, data=self.in_data)
        response = self.processor.check_response_ex(data_cmd)
        if not response[0]:
            raise ValueError("send data failed")

    def get_data(self):
        get_data_cmd = CommandStruct(cmd=ServerCommand.Com_Get_Data)
        response = self.processor.check_response_ex(get_data_cmd)
        outdata = response[1].data
        if not response[0]:
            raise ValueError("get data failed")
        else:
            if isinstance(self.out_data, type([])):
                self.out_data.append(outdata)

    def stop_slave(self):
        stop_mining_cmd = CommandStruct(cmd=ServerCommand.Com_Stop_Mining)
        response = self.processor.check_response_ex(stop_mining_cmd)
        if not response[0]:
            raise ValueError("stop slave failed")

    def setup_slave(self):
        setup_cmd = CommandStruct(cmd=ServerCommand.Com_Setup, data=self.in_data)
        response = self.processor.check_response_ex(setup_cmd)
        if not response[0]:
            raise ValueError("send data failed")

    def clear_cache(self):
        stop_mining_cmd = CommandStruct(cmd=ServerCommand.Com_Clear_Cache)
        response = self.processor.check_response_ex(stop_mining_cmd)
        if not response[0]:
            raise ValueError("clear cache failed")

    def run(self):
        try:
            start_cmd = CommandStruct(ServerCommand.Com_Start)
            stop_cmd = CommandStruct(ServerCommand.Com_Stop)
            if self.is_connection_ok() and self.processor.check_response_ex(start_cmd)[0]:
                if self.cmd == ServerCommand.Com_Status:
                    self.get_status()
                elif self.cmd == ServerCommand.Com_Data:
                    self.send_data()
                elif self.cmd == ServerCommand.Com_Get_Data:
                    self.get_data()
                elif self.cmd == ServerCommand.Com_Stop_Mining:
                    self.stop_slave()
                elif self.cmd == ServerCommand.Com_Setup:
                    self.setup_slave()
                elif self.cmd == ServerCommand.Com_Clear_Cache:
                    self.clear_cache()
                else:
                    pass
            try:  # the last call may have exception due to network connection problem
                self.processor.check_response_ex(stop_cmd)
            except:
                pass

        except Exception as ex:
            print(ex)
            pass


class MiningMasterController(threading.Thread):

    def __init__(self, ref="", cap_slave=0, cap_slave_process=1, cap_concurrent_page=1, all_job=0, offset = 0, max_page_level=100, max_page_limit=1000,
                 loopback_database=True, refresh_rate=10, min_page_count=0, filters=DBFilterCollection()):
        """
        init a master controller
        :param ref: dataBase Table reference
        :param cap: max number of slaves
        :param all_job:
        :return:
        """
        threading.Thread.__init__(self)
        self.state = ServerState.State_Init
        self.ref = ref  # database
        self.slaves = []
        self.auto_scale_slaves(cap_slave)
        self.cap_slave_process = cap_slave_process  # how many process can a slave run, if it is 0, then it will auto scale
        self.concurrent_page = cap_concurrent_page
        self.stop_Mining = False
        self.job_done = 0
        self.job_wait = 0
        self.job_allocated = 0
        self.job_all = all_job
        self.offset = offset
        self.max_page_level = max_page_level
        self.max_page_limit = max_page_limit
        self.start_time = time.time()
        self.end_time = time.time()
        self.loopback_database = loopback_database
        self.refresh_rate = refresh_rate
        self.in_progress = False
        self.min_page_count = min_page_count  # only crawl sites with page greater than this number

        self.db_seed = None
        if filters is None:
            self.db_filters = DBFilterCollection()
        else:
            self.db_filters = filters
        self.filter_shadow = filters.copy_attrs()
        self.db_stats = []
        self.seed_db_update_time = time.time()
        self.external_db_update_time = time.time()
        self.filtered_db_update_time = time.time()
        self.db_update_lock = threading.RLock()
        self._seed_db_lock = RLock()
        self._external_db_lock = RLock()
        self._result_db_lock = RLock()
        self._result_bad_db_lock = RLock()
        self._redemption_db_lock = RLock()
        self.update_db_stats(force_update=True)
        self._stop_event = Event()

        #this is for filters
        self._filter_input_queue = Queue()
        self._filter_output_queue = Queue()
        self.filter_process = None
        self._filter_matrix = FilteredDomainData(tf=15, cf=15, da=10, ref_domains=10, tf_cf_deviation=0.44)
        self._majestic_filter_on = False

    def update_db_stats(self, force_update=False):
        print("update db stats, do not interrupt!")
        if self.filter_shadow is not None:
            names = SiteSource.get_all_table_names(SiteSource.Seed)
            if len(names) > 0:
                databases = []
                fil = self.filter_shadow
                if force_update:
                    for name in names:
                        if name is not None and len(name) > 0:
                            with self._seed_db_lock:
                                seed = SeedSiteDB(name, db_filter=fil.seed_filter)
                                seed_count = seed.site_count()
                                seed.close()
                            with self._external_db_lock:
                                external = ExternalSiteDB(name, db_filter=fil.external_filter)
                                external_count = external.site_count()
                                external.close()
                            with self._result_db_lock:
                                filtered = FilteredResultDB(name, db_filter=fil.filtered_result)
                                filtered_count = filtered.site_count()
                                filtered.close()
                            with self._result_bad_db_lock:
                                filtered_bad = FilteredResultDB(name, bad_db=True, db_filter=fil.filtered_result)
                                filtered_count_bad = filtered_bad.site_count()
                                filtered_bad.close()
                            x = DatabaseStatus(name, seed_count, external_count, filtered_count, filtered_count_bad)
                            databases.append(x)
                    self.seed_db_update_time = time.time()
                    self.external_db_update_time = time.time()
                    self.filtered_db_update_time = time.time()
                    self.db_stats = databases
                    #return databases
                else:
                    time_now = time.time()
                    if len(self.db_stats) == 0:
                        for name in names:
                            self.db_stats.append(DatabaseStatus(name=name))
                    else:
                        dying_db = [x for x in self.db_stats if x.name not in names]
                        for item in dying_db:
                            self.db_stats.remove(item)
                    external_need_update = True if time_now - self.external_db_update_time > fil.external_filter.update_interval else False
                    if external_need_update:
                        self.external_db_update_time = time.time()
                    seed_need_update = True if time_now - self.seed_db_update_time > fil.seed_filter.update_interval else False
                    if seed_need_update:
                        self.seed_db_update_time = time.time()
                    filterd_need_update = True if time_now - self.filtered_db_update_time > fil.filtered_result.update_interval else False
                    if filterd_need_update:
                        self.filtered_db_update_time = time.time()
                    for name in names:  # update stats
                        db_s = next((x for x in self.db_stats if name == x.name), None)
                        if db_s is None and len(name) > 0:
                            db_s = DatabaseStatus(name)
                            self.db_stats.append(db_s)
                        if db_s is not None:
                            if seed_need_update:
                                seed = SeedSiteDB(name, db_filter=fil.seed_filter)
                                db_s.seeds = seed.site_count()
                                seed.close()
                            if external_need_update:
                                external = ExternalSiteDB(name, db_filter=fil.external_filter)
                                db_s.results = external.site_count()
                                external.close()
                            if filterd_need_update:
                                filtered = FilteredResultDB(name, db_filter=fil.filtered_result)
                                db_s.filtered = filtered.site_count()
                                filtered.close()

                                filtered_bad = FilteredResultDB(name, bad_db=True, db_filter=fil.filtered_result)
                                db_s.bad_filtered = filtered_bad.site_count()
                                filtered_bad.close()
                    #return self.db_stats
            else:
                pass
                #return []

        else:
            pass
            #return []
        print("update db stats completed")

    def remove_db(self, db_type: str, db_name: str):
        if db_type == DBType.Type_All:
            with self._seed_db_lock:
                seed = SeedSiteDB(db_name)
                seed.drop_table()
                seed.close()
            with self._external_db_lock:
                external = ExternalSiteDB(db_name)
                external.drop_table()
                external.close()
            with self._result_db_lock:
                filtered = FilteredResultDB(db_name)
                filtered.drop_table()
                filtered.close()
            with self._result_bad_db_lock:
                filtered_bad = FilteredResultDB(db_name, bad_db=True)
                filtered_bad.drop_table()
                filtered_bad.close()

        elif db_type == DBType.Type_External:
            with self._external_db_lock:
                external = ExternalSiteDB(db_name)
                external.drop_table()
                external.close()

        elif db_type == DBType.Type_Filtered_Result:
            with self._result_db_lock:
                filtered = FilteredResultDB(db_name)
                filtered.drop_table()
                filtered.close()
        elif db_type == DBType.Type_Filtered_Result_Bad:
            with self._result_bad_db_lock:
                filtered_bad = FilteredResultDB(db_name, bad_db=True)
                filtered_bad.drop_table()
                filtered_bad.close()

        self.update_db_stats(force_update=True)

    def add_seeds(self, seed):
        if isinstance(seed, MiningList):
            try:
                with self._seed_db_lock:
                    db = SeedSiteDB(seed.ref)
                    db.add_sites(seed.data)
                    db.close()
                self.update_db_stats(force_update=True)
            except Exception as ex:
                ErrorLogger.log_error("MiningMasterController.add_seeds()", ex, seed.ref)

    def get_db_stats(self):
        #print("copy db stats and send back")
        stats = MiningList(self.ref, self.db_stats)
        stats_copy = stats.copy_attrs()
        print("copy db stats completed")
        return stats_copy

    def get_filter_progress(self):
        if isinstance(self.filter_process, MemoryControlPs):
            state = self.filter_process.get_last_state()
            if isinstance(state, _FilterState):
                return state.progress, state.all_data
            else:
                return 0, 0
        else:
            return 0, 0

    def clear_host_cache(self):
        try:
            FileHandler.clear_dir(get_log_dir())
            FileHandler.clear_dir(get_recovery_dir_path())
            FileHandler.clear_dir(get_task_backup_dir())
            FileHandler.clear_dir(get_db_buffer_default_dir())
        except Exception as ex:
            ErrorLogger.log_error("MiningControllers", ex, "clear_host_cache()")

    def clear_slave_cache(self):
        if self.state == ServerState.State_Idle:
            threads = []
            for slave in self.slaves:
                if isinstance(slave, Server):
                    threads.append(MiningController(slave, cmd=ServerCommand.Com_Clear_Cache))
            if len(threads) > 0:
                for thread in threads:
                    thread.start()
                for thread in threads:
                    thread.join()
                threads.clear()

    def get_db_seed(self):
        return SeedSiteDB(table=self.ref, offset=0, db_filter=self.db_filters.seed_filter)

    def get_db_external(self):
        return ExternalSiteDB(table=self.ref, offset=0, db_filter=self.db_filters.external_filter)

    def get_db_filtered(self):
        return FilteredResultDB(table=self.ref, offset=0, db_filter=self.db_filters.filtered_result)

    def get_db_filtered_bad(self):
        return FilteredResultDB(table=self.ref, offset=0, bad_db=True, db_filter=self.db_filters.filtered_result)

    def get_db_redemption(self):
        return ExternalSiteDB(table="temp", db_addr=get_temp_db_dir()+"Redemption.db")

    def get_db_results(self, db_type: str, db_name: str, index: int, length: int) -> MiningList:
        try:
            if db_type == DBType.Type_Filtered_Result:
                with self._result_db_lock:
                    db = FilteredResultDB(db_name, offset=index)
                    data = db.get_next_patch(count=length, rollover=False)
                    db.close()
            elif db_type == DBType.Type_Filtered_Result_Bad:
                with self._result_bad_db_lock:
                    db = FilteredResultDB(db_name, bad_db=True, offset=index)
                    data = db.get_next_patch(count=length, rollover=False)
                    db.close()
            elif db_type == DBType.Type_External:
                with self._external_db_lock:
                    db = ExternalSiteDB(db_name, offset=index)
                    data = db.get_next_patch(count=length, rollover=False)
                    db.close()
            elif db_type == DBType.Type_Seed:
                with self._seed_db_lock:
                    db = SeedSiteDB(db_name, offset=index)
                    data = db.get_next_patch(count=length, rollover=False)
                    db.close()
            else:
                data = []
            result = MiningList(db_name, data)
            return result
        except Exception as ex:
            ErrorLogger.log_error("MiningController.get_db_results()", ex, db_name + " type:" + db_type)
            return MiningList(db_name, [])

    def auto_scale_slaves(self, count: int):
        pass

    def stop_all_slave(self):
        threads = []
        for slave in self.slaves:
            if isinstance(slave, Server):
                threads.append(MiningController(slave, cmd=ServerCommand.Com_Stop_Mining))
        if len(threads) > 0:
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            threads.clear()

    def setup_minging_slaves(self): # salve should restart based on this new settings
        threads = []
        for slave in self.slaves:
            if isinstance(slave, Server):
                threads.append(MiningController(slave, cmd=ServerCommand.Com_Setup,
                                                in_data=SetupData(self.name, cap2=self.cap_slave_process,
                                                                  cap3=self.concurrent_page,
                                                                  max_page_level=self.max_page_level,
                                                                  max_page_limit=self.max_page_limit)))
        if len(threads) > 0:
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            threads.clear()

    def check_slaves_status(self):
        threads = []
        for slave in self.slaves:
            if isinstance(slave, Server):
                threads.append(MiningController(slave, cmd=ServerCommand.Com_Status))
        if len(threads) > 0:
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            threads.clear()
        total_done = 0  # update number of job done, and job wait
        wait = 0
        for slave in self.slaves:
            if isinstance(slave, Server):
                print(slave.status)
                total_done += slave.status.done_job
                wait += slave.status.wait_job
        if total_done > self.job_done:
            self.job_done = total_done
        self.job_wait = wait

    @staticmethod
    def is_in_list(data, target_list: []):
        if len(target_list):
            target = next((x for x in target_list if data.domain == x.domain), None)
            return True if target is not None else False
        else:
            return False

    def get_slaves_result(self) -> []:
        threads = []
        result = []
        resultList = []
        for slave in self.slaves:
            if isinstance(slave, Server):
                if isinstance(slave.status, dict):
                    print("in get_slaves_result, data type is wrong")
                    print(slave.status)
                    slave.status = Serializable.get_deserialized(slave.status)
                elif slave.status is not None and slave.status.result > 0:
                    result_holder = []
                    threads.append(MiningController(slave, cmd=ServerCommand.Com_Get_Data, out_data=result_holder))
                    result.append(result_holder)
        if len(threads) > 0:
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            threads.clear()
            if len(result) > 0:
                for item in result:
                    if len(item) > 0 and hasattr(item[0], "data"):  # data is the attribute of MiningList
                        data = getattr(item[0], "data")
                        resultList += data
        return resultList

    def is_in_slave_list(self, addr: str) -> True:
        if addr != "":
            match = next((x for x in self.slaves if x.address.address == addr), None)
            return True if match is not None else False
        else:
            return False

    def add_slaves(self, slaves: []):
        if slaves is not None:
            for slave in slaves:
                if isinstance(slave, ServerAddress):
                    if slave.address == "localhost":
                        slave.address = "127.0.0.1"
                    if self.is_in_slave_list(slave.address):
                        continue
                    ser = Server(server_type=ServerType.ty_MiningSlaveSmall, address=slave)
                    self.slaves.append(ser)
                elif isinstance(slave, str):
                    temp = slave
                    if slave == "localhost":
                        temp = "127.0.0.1"
                    if self.is_in_slave_list(slave):
                        continue
                    ser = Server(server_type=ServerType.ty_MiningSlaveSmall, address=ServerAddress(temp, MiningTCPServer.DefaultListenPort))
                    self.slaves.append(ser)

    def remove_slaves(self, slaves: []):
        if slaves is not None:
            for slave in slaves:
                found = None
                if isinstance(slave, ServerAddress):
                    found = next(x for x in self.slaves if x.address.address == slave.address)
                elif isinstance(slave, str):
                    found = next(x for x in self.slaves if x.address.address == slave)
                if found is not None:
                    self.slaves.remove(found)

    def get_slaves(self):
        return self.slaves

    def allocate_task(self):
        try:
            threads = []
            with self._seed_db_lock:
                db_seed = SeedSiteDB(offset=self.offset, table=self.ref, db_filter=self.db_filters.seed_filter)
                for slave in self.slaves:
                    if isinstance(slave, Server) and slave.status is not None:
                        if isinstance(slave.status, dict):
                            print("in allocate_task, data type is invalid, the following data was received, need to redo")
                            print(slave.status)
                            slave.status = Serializable.get_deserialized(slave.status)
                            #raise ValueError("slave status is not valid data type")
                        if slave.status.all_job - slave.status.done_job <= slave.status.cap_process + 2 > 2:
                            job_temp = int(slave.status.cap_process/2)  # give half an 1/4 hour worth of data
                            if job_temp < 5:  # give minimum of 5 jobs
                                job_temp = 5
                            if not self.loopback_database and job_temp + self.job_allocated > self.job_all:
                                job_temp = self.job_all - self.job_allocated
                            sites = db_seed.get_next_patch(count=job_temp, rollover=self.loopback_database)
                            print("allocate task:")
                            print(sites)
                            self.job_allocated += len(sites)
                            ref = db_seed.tab
                            mlist = MiningList(ref, sites)
                            number_sites = len(sites)
                            if number_sites > 0:
                                try:
                                    CsvLogger.log_to_file(slave.address.address, [(link,) for link in sites],
                                                          dir_path=get_task_backup_dir())
                                except:
                                    pass
                                self.offset += number_sites
                                threads.append(MiningController(slave, cmd=ServerCommand.Com_Data, in_data=mlist))
                            else:
                                return
                db_seed.close()
            if len(threads) > 0:
                for thread in threads:
                    thread.start()
                for thread in threads:
                    thread.join()
            threads.clear()
        except Exception as ex:
            ErrorLogger.log_error("MiningMasterController.allocate_task()", ex, self.ref)

    def process_filtering_output_results(self):
        results = []
        bad_results = []
        tuples = []
        while not self._filter_output_queue.empty():
            item = self._filter_output_queue.get()
            if isinstance(item, FilteredDomainData):
                if len(item.exception) > 0:
                    bad_results.append(item)
                else:
                    results.append(item)
                tuples.append(item.to_tuple())
        if len(results) > 0:
            try:
                with self._result_db_lock:
                    db = self.get_db_filtered()
                    db.add_sites(results, skip_check=False)
                    db.close()
            except Exception as ex:
                ErrorLogger.log_error("MingingMasterController", ex, "process_filtering_output_results() " + self.ref)
            finally:
                CsvLogger.log_to_file("filtered_domains.csv", tuples)
        if len(bad_results) > 0:
            try:
                with self._result_bad_db_lock:
                    bad_db = self.get_db_filtered_bad()
                    bad_db.add_sites(bad_results, skip_check=False)
                    bad_db.close()
            except Exception as ex:
                ErrorLogger.log_error("MingingMasterController", ex, "process_filtering_output_results() " + self.ref)
            finally:
                CsvLogger.log_to_file("filtered_domains.csv", tuples)

    def process_result(self, result: []):
        if result is not None and len(result) > 0:
            print("processing external site and seeds results")
            external = []
            sitesfeedback = []
            redemption_list = []
            try:
                for item in result:
                    #print("item: ", str(item.__dict__))
                    if isinstance(item, ScrapeDomainData):
                        #print(item)
                        #if not MiningMasterController.is_in_list(item, external) and not all_external.is_domain_in_db(item.domain):
                        raw_data = (item.domain, item.code)
                        if item.code == ResponseCode.MightBeExpired:
                            redemption_list.append(raw_data)
                        else:
                            external.append(raw_data)
                            self._filter_input_queue.put(raw_data)  # also put into filtering queue
                    elif isinstance(item, SeedSiteFeedback):
                        #print("udpate:", str(item.__dict__))
                        sitesfeedback.append(item)
                    else:
                        continue
                with self._external_db_lock:
                    all_external = self.get_db_external()
                    all_external.add_sites(external, True)
                    all_external.close()
                with self._redemption_db_lock:
                    redemption_db = self.get_db_redemption()
                    redemption_db.add_sites(redemption_list, True)
                    redemption_db.close()
                with self._seed_db_lock:
                    seed_sites = self.get_db_seed()
                    seed_sites.update_sites(sitesfeedback)
                    seed_sites.close()
            except Exception as ex:
                ErrorLogger.log_error("MingingMasterController", ex, "process_result() " + self.ref)

    def pause(self):
        self.in_progress = False
        self.stop_all_slave()
        self.stop_Mining = True

    def stop(self):
        print("external set to stop!")
        self._stop_event.set()
        self.in_progress = False
        self.stop_all_slave()

    def continue_work(self):
        self.stop_Mining = False

    def _filtering_process_wrapper(self):
        self.filter_process = MemoryControlPs(func=filtering_process,
                                         func_kwargs=FilterController.get_input_parameters("filtering.db", get_db_buffer_default_dir(), self._filter_input_queue,
                                                                                           self._filter_output_queue, self._stop_event,
                                                                                           self._filter_matrix,
                                                                                           self._majestic_filter_on),
                                         external_stop_event=self._stop_event)
        self.filter_process.start()

    def run(self):  # this is the nornal routine, should setup slaves before doing this
        filter_t = threading.Thread(target=self._filtering_process_wrapper)
        if len(self.slaves) > 0:
            filter_t.start()

        while not self._stop_event.is_set():
            self.state = ServerState.State_Idle
            print("check status")
            self.check_slaves_status()
            #time.sleep(1)
            if not self.stop_Mining and len(self.slaves) > 0:
                self.state = ServerState.State_Active
                print("allocate task")
                self.allocate_task()
                #time.sleep(1)
                print("get and process results")
                result = self.get_slaves_result()
                self.process_result(result)
                result.clear()
                self.process_filtering_output_results() # get filtered result into Filtered DB
                if (self.loopback_database or self.job_done < self.job_all) and len(self.slaves) > 0:
                    self.end_time = time.time()
                    self.in_progress = True
                else:
                    self.in_progress = False
                print("finished getting results")
            self.update_db_stats()
            print("update db finished")
            if self._stop_event.is_set():
                break
            time.sleep(15)
        print("should finish filtering process!")
        if filter_t.is_alive():
            filter_t.join()
        print("master server shut down!")


