import multiprocessing
from multiprocessing.pool import ThreadPool
from threading import Thread
from DomainFinderSrc.Scrapers.SiteChecker import SiteCheckerController, SiteFeedback
from DomainFinderSrc.Scrapers.SiteTempDataSrc.SiteTempDataSrcInterface import OnSiteLink
from DomainFinderSrc.Scrapers.SiteThreadChecker import SiteThreadChecker
from DomainFinderSrc.Scrapers.SiteCheckerManager import outputThread
from DomainFinderSrc.Utilities.MemoryControlProcess import MemoryControlPs
from DomainFinderSrc.Scrapers.SiteTempDataSrc.DBStruct import SiteTempDatabase, TempDBInterface
from DomainFinderSrc.Utilities.FilePath import *
from DomainFinderSrc.Utilities.Logging import *
from DomainFinderSrc.Scrapers.ExternalSiteChecker import WhoisChecker, WhoisCheckerState
from DomainFinderSrc.Utilities.QueueManager import *
from multiprocessing import Process


class process_iter_arg:
    def __init__(self, func, func_arg=(), func_kwarg=None, callback=None, Memlimit=200, external_stop=None):
        self.func = func
        self.func_arg = func_arg
        self.func_kwarg = func_kwarg
        self.callback =callback
        self.Memlimit = Memlimit
        self.external_stop = external_stop


def site_check_process(*args, **kwargs):
    site_checker = SiteThreadChecker(*args, **kwargs)
    site_checker.crawling()


def whois_process(*args, **kwargs):
    checker = WhoisChecker(*args, **kwargs)
    checker.run_farm()


def site_check_process_wraper(func, func_arg=(), func_kwarg=None, callback=None, Memlimit=200, external_stop=None):
    mem_pro = MemoryControlPs(func, func_arg, func_kwarg, callback, Memlimit, external_stop)
    mem_pro.start()


def site_check_process_iter(obj: process_iter_arg):
    site_check_process_wraper(func=obj.func, func_arg=obj.func_arg, func_kwarg=obj.func_kwarg, callback=obj.callback,
                              Memlimit=obj.Memlimit, external_stop=obj.external_stop)


class SiteInputIter(object):
    def __init__(self, input_queue: multiprocessing.Queue,
                 func, external_stop:multiprocessing.Event, func_arg=(), func_kwarg: dict=None,
                 callback=None, Memlimit=200):
        self.queue = input_queue
        self.func = func
        self.func_arg = func_arg
        if func_kwarg is None:
            self.func_kwarg = {}
        else:
            self.func_kwarg = func_kwarg
        self.callback = callback
        self.Memlimit = Memlimit
        self.external_stop = external_stop

        self.continue_lock = threading.RLock()

    def can_continue(self):
        with self.continue_lock:
            stop = self.external_stop.is_set()
        return not stop

    def __next__(self):
        return_obj = None
        while self.can_continue():
            if not self.queue.empty():
                return_obj = self.queue.get()
                break
            else:
                time.sleep(0.5)

        if return_obj is None:
            raise StopIteration
        else:
            copy_kwarg = self.func_kwarg.copy()  # shadow copy of the object
            copy_kwarg.update({SiteThreadChecker.full_link_key: return_obj})
            return_arg = process_iter_arg(self.func, self.func_arg, copy_kwarg, self.callback, self.Memlimit,
                                          self.external_stop)
            return return_arg

    def __iter__(self):
        return self


class SiteCheckProcessState:
    def __init__(self, job_all: int, job_done: int, job_wait: int, total_page_done: int, average_page: float,
                 result_count: int):
        self.job_all = job_all
        self.job_done = job_done
        self.job_wait = job_wait
        self.total_page_done = total_page_done
        self.average_page = average_page
        self.result_count = result_count


def run_queue_server():
    server = get_queue_server(QueueManager.MachineSettingCrawler)
    server.serve_forever()


class SiteCheckProcessManager(Thread, SiteCheckerController):
    MEM_MINIMUM_REQ = 100
    def __init__(self, job_name: str="", input_Q:multiprocessing.Queue=None, max_procss=4, concurrent_page=1,
                 page_max_level=10, max_page_per_site=1000, output_delegate=None,
                 memory_limit_per_process=100, **kwargs):
        """

        :param job_name:
        :param input_Q:
        :param max_procss:
        :param concurrent_page:
        :param page_max_level:
        :param max_page_per_site:
        :param output_delegate:
        :param memory_limit_per_process: if value is less than 100, throw ValueException
        :param kwargs:
        :return:
        """
        Thread.__init__(self)
        #FeedbackInterface.__init__(**kwargs)
        #super(SiteCheckProcessManager, self).__init__(**kwargs)
        #self.process_queue = multiprocessing.Queue()
        self.name = job_name
        if max_procss <= 0:
            max_procss = 1
        self.max_prcess = max_procss
        if input_Q is None:
            self.inputQueue = multiprocessing.Queue()
        else:
            self.inputQueue = input_Q
        self.outputQueue = multiprocessing.Queue()
        self._whoisQueue = multiprocessing.Queue(maxsize=100000)
        #self.output_lock = threading.RLock()
        #self.tempList = site_list # if there is a need to add new sites during scripting, add to this list
        self.processPrfix = "Process-"
        self.threadPrfix = "Thread-"
        self.page_max_level = page_max_level
        self.max_page_per_site = max_page_per_site

        if output_delegate is None:
            self.output_delegate = self.default_delegate
        else:
            self.output_delegate = output_delegate # delegate of type f(x:OnSiteLink)
        self.stop_event = multiprocessing.Event()
        self.finished = False
        self.pool = ThreadPool(processes=self.max_prcess)
        #self.pool = multiprocessing.Pool(processes=self.max_prcess)
        self.output_thread = outputThread(0, self.threadPrfix+"Output", self.stop_event, self.outputQueue,
                                          delegate=self.output_delegate)
        self.job_all = 0
        self.job_done = 0
        self.job_waiting = 0
        self.total_page_done = 0
        self.page_per_sec = 0  # need to do this
        self.average_page_per_site = 0
        self.patch_limit = self.max_prcess
        self.temp_results = []
        self.site_info = []  # collect site info after the job done
        self.db_trash_list = []
        self.concurrent_page = concurrent_page
        self.continue_lock = threading.RLock()
        self.db_trash_lock = threading.RLock()
        self.state_lock = threading.RLock()
        self.temp_result_lock = threading.RLock()
        self.site_info_lock = threading.RLock()
        if memory_limit_per_process < SiteCheckProcessManager.MEM_MINIMUM_REQ:
            ex = ValueError("minimum memory requirement to run the crawler is 100 MB, otherwise too many memory control looping.")
            msg = "error in SiteCheckProcessManager.__init__(), with database: " + job_name
            ErrorLogger.log_error("SiteCheckProcessManager", ex, msg)
        self.memory_limit_per_process = memory_limit_per_process
        self.whois_process = None
        self.whois_queue_process = Process(target=run_queue_server)
        #self.input_iter = SiteInputIter(self.inputQueue, self, self.concurrent_page, self.page_max_level,
        #                                self.max_page_per_site, self.outputQueue, self.process_site_info)
        self.input_iter = SiteInputIter(self.inputQueue, func=site_check_process, external_stop=self.stop_event)

    def clear_cache(self):
        try:
            FileHandler.clear_dir(get_log_dir())
            FileHandler.clear_dir(get_recovery_dir_path())
            FileHandler.clear_dir(get_temp_db_dir())
            FileHandler.clear_dir(get_task_backup_dir())
            FileHandler.clear_dir(get_db_buffer_default_dir())
        except Exception as ex:
            ErrorLogger.log_error("SiteCheckProcessManager", ex, "clear_cache()")

    def get_temp_result_count(self):
        #with self.temp_result_lock:
        return len(self.temp_results)

    def get_temp_result_and_clear(self) -> []:
        with self.temp_result_lock:
            copied = self.temp_results.copy()
            self.temp_results.clear()
        return copied

    def default_delegate(self, result):
        with self.temp_result_lock:
            if isinstance(result, OnSiteLink):
                self.temp_results.append(result)  # make no difference
                #CsvLogger.log_to_file("ExternalSiteTemp", [(result.link, result.response_code), ])
            elif isinstance(result, str):
                self.temp_results.append(result)
            else:
                pass

    def get_state(self) -> SiteCheckProcessState:
        with self.state_lock:
            state = SiteCheckProcessState(self.job_all, self.job_done, self.job_waiting, self.total_page_done,
                                          self.average_page_per_site, self.get_temp_result_count())
        return state

    def get_filter_progress(self):
        if isinstance(self.whois_process, MemoryControlPs):
            state = self.whois_process.get_last_state()
            if isinstance(state, WhoisCheckerState):
                return state.progress_count, state.data_total
            else:
                return 0, 0
        else:
            return 0, 0

    def clear_trash(self):  # run with a thread
        while not self.stop_event.is_set():
            with self.db_trash_lock:
                removed_list = []
                trash_len = len(self.db_trash_list)
                if trash_len > 0:
                    for item in self.db_trash_list:
                        if TempDBInterface.force_clear(item):
                            #print("removed trash:", item)
                            removed_list.append(item)
                    for removed_item in removed_list:
                        self.db_trash_list.remove(removed_item)
                    CsvLogger.log_to_file("job_finished", [(x, str(datetime.datetime.now())) for x in removed_list], get_task_backup_dir())
                    removed_list.clear()
            time.sleep(2)

    def put_to_input_queue(self, data: []):
        if data is not None:
            for item in data:
                self.inputQueue.put(item)
                self.job_all += 1

    def get_site_info_list_and_clear(self):
        with self.site_info_lock:
            copied = self.site_info.copy()
            self.site_info.clear()
        return copied

    def get_site_info_list_count(self):
        return len(self.site_info)

    def process_site_info(self, site_info):
        if site_info is not None:
            with self.site_info_lock:
                #print("new site info: ", site_info.__dict__)
                self.site_info.append(site_info)

    def process_feedback(self, feedback: SiteFeedback):
        self.add_page_done(feedback.page_done)
        if feedback.finished:
            # print("should process feedback!")
            self.site_finished()
            self.process_site_info(feedback.seed_feedback)
            with self.db_trash_lock:
                self.db_trash_list.append(feedback.datasource_ref)
                self.db_trash_list.append(feedback.datasource_ref+".ext.db")

    def add_page_done(self, number_page_done: int):  # make sure it is thread safe
        with self.state_lock:
            self.total_page_done += number_page_done

    def site_finished(self):
        # print("one more site done")
        with self.state_lock:
            self.job_done += 1
            self.average_page_per_site = self.total_page_done/self.job_done

    def set_stop(self):
        self.stop_event.set()

    def can_continue(self):
        return not self.stop_event.is_set()

    def checking_whois(self):
        optinmal = self.max_prcess * self.concurrent_page/5
        if optinmal < 10:
            worker_number = 10
        else:
            worker_number = int(optinmal)
        mem_limit = self.memory_limit_per_process/2
        if mem_limit < 200:
            mem_limit = 200
        self.whois_process = MemoryControlPs(whois_process,
                                      func_kwargs=WhoisChecker.get_input_parameters(self._whoisQueue, self.outputQueue,
                                                                                    self.stop_event, worker_number),
                                      mem_limit=mem_limit, external_stop_event=self.stop_event)
        self.whois_process.start()

    def run(self):
        whois_thread = Thread(target=self.checking_whois)
        trash_clean_thread = Thread(target=self.clear_trash)
        self.output_thread.start()
        trash_clean_thread.start()
        whois_thread.start()
        self.whois_queue_process.start()
        self.input_iter.func_kwarg = SiteThreadChecker.get_input_parameter(full_link="", # this parameter will be updated in self.input_iter
                                                                           max_page=self.max_page_per_site,
                                                                           max_level=self.page_max_level,
                                                                           output_queue=self._whoisQueue,
                                                                           pool_size=self.concurrent_page)
        self.input_iter.callback = self.process_feedback
        self.input_iter.Memlimit = self.memory_limit_per_process
        try:
            #print("monitor process started: pid: ", os.getpid())
            self.pool.imap(site_check_process_iter, self.input_iter, 1)
            #self.pool.imap_unordered(site_check_process_iter, self.input_iter)
            while self.can_continue():
                time.sleep(0.5)
        except Exception as ex:
            msg = "run(), with database: " + self.name
            ErrorLogger.log_error("SiteCheckProcessManager", ex, msg)
        finally:
            print("terminate miner!")
            self.pool.terminate()
            whois_thread.join()
            self.whois_queue_process.terminate()
            self.temp_results.clear()
            self.site_info.clear()
            self.finished = True

