from DomainFinderSrc.Scrapers.LinkChecker import LinkChecker
from DomainFinderSrc.Utilities.MemoryControlProcess import FeedbackInterface
from DomainFinderSrc.Utilities.Logging import ErrorLogger, ProgressLogger, ProgressLogInterface
from DomainFinderSrc.Scrapers.SiteTempDataSrc.ExternalTempDataDiskBuffer import \
    ExternalTempDataDiskBuffer, ExternalTempInterface
from DomainFinderSrc.Scrapers.SiteTempDataSrc.SiteTempDataSrcInterface import OnSiteLink, ResponseCode
from multiprocessing import Queue, Event
from multiprocessing.pool import ThreadPool
from threading import RLock
import time
import threading
from DomainFinderSrc.Scrapers.TLDs import TldUtility
import multiprocessing
from DomainFinderSrc.Utilities.QueueManager import *


class WhoisCheckerState:
    def __init__(self, progress_count: int, data_total: int):
        self.progress_count = progress_count
        self.data_total = data_total


class WhoisChecker(FeedbackInterface, ExternalTempInterface, ProgressLogInterface):
    """
    usage:
    checker = WhoisChecker(...)
    checker.run_farm()
    """
    def __init__(self, stop_event: Event, input_queue: Queue=None, output_queue: Queue=None,
                 max_worker: int=10, dir_path="", is_debug=False,  **kwargs):
        self._is_debug = is_debug
        FeedbackInterface.__init__(self, **kwargs)
        ExternalTempInterface.__init__(self)
        # do not use predefined queue here
        # self._input_q = input_queue
        # self._output_q = output_queue
        self._stop_event = stop_event
        self._internal_stop_event = Event()
        self._max_worker = max_worker
        self._job_done = 0
        self._job_done_shadow = 0
        self._job_done_lock = RLock()
        self._input_period = 0.0001  # time to sample data into the buffer
        self._max_sample_results = 100000
        self._min_sampling_duration = 0.0001
        self._sample_batch_size = 5000
        self._sample_batch_timeout = 60
        if is_debug:
            self._min_buff_delete_threshold = 10000  # default is 100000
        else:
            self._min_buff_delete_threshold = 100000
        self._speed_penalty_count = 0
        self._finished = False
        manager, self._output_q = get_queue_client(QueueManager.MachineSettingCrawler, QueueManager.Method_Whois_Output)
        self._db_buffer = ExternalTempDataDiskBuffer("whois_check.db", self, self._internal_stop_event, buf_size=self._max_worker*50,
                                                     terminate_callback=WhoisChecker.terminate_callback, dir_path=dir_path)
        self._populate_with_state()  # FeedbackInterface
        if not is_debug:
            log_period = 120
        else:
            log_period = 10
        self._progress_logger = ProgressLogger(log_period, self, self._internal_stop_event)

    @staticmethod
    def terminate_callback():
        ErrorLogger.log_error("WhoisChecker", StopIteration("terminated."))

    @staticmethod
    def get_input_parameters(input_queue: Queue, output_queue: Queue, stop_event: Event, max_worker: int=20) -> dict:
        return {"input_queue": input_queue, "output_queue": output_queue, "stop_event": stop_event,
                "max_worker": max_worker}

    def get_job_done_count(self):
        with self._job_done_lock:
            job_done = self._job_done
        return job_done

    def _add_job_done_one(self):
        with self._job_done_lock:
            self._job_done += 1

    def _put_output_result_in_queue(self, domain_data: OnSiteLink):
        if not self._stop_event.is_set() or not self._internal_stop_event.is_set():
            try:
                self._output_q.put((domain_data.link, domain_data.response_code))
            except Exception as inner_ex:
                if self._output_q is None:
                    manager, self._output_q = get_queue_client(QueueManager.MachineSettingCrawler, QueueManager.Method_Whois_Output)
                ErrorLogger.log_error("WhoisChecker", inner_ex, addtional="failed to put result in queue.")
                time.sleep(0.01)
                self._put_output_result_in_queue(domain_data)

    def _check_whois_v1(self, domain_data: OnSiteLink):
        root_domain = domain_data.link
        try:
            if root_domain.startswith("http"):
                root_domain = LinkChecker.get_root_domain(domain_data.link)[1]
            real_response_code = domain_data.response_code
            whois = LinkChecker.check_whois(root_domain)  # check whois record
            if whois[0]:
                if whois[2]:  # domain is expired
                    real_response_code = ResponseCode.Expired
                else:
                    real_response_code = ResponseCode.MightBeExpired
            if real_response_code == ResponseCode.Expired:
            #if ResponseCode.domain_might_be_expired(real_response_code):
                domain_data.link = root_domain
                domain_data.response_code = real_response_code
                #return_obj = OnSiteLink(root_domain, real_response_code, domain_data.link_level, OnSiteLink.TypeOutbound)
                # if isinstance(self._queue_lock, multiprocessing.RLock):
                with self._queue_lock:
                    self._output_q.put((domain_data.link, domain_data.response_code))
        except Exception as ex:
            ErrorLogger.log_error("ExternalSiteChecker.WhoisChecker", ex, "_check_whois() " + root_domain)
        finally:
            self._add_job_done_one()

    def _check_whois(self, domain_data: OnSiteLink):
        root_domain = domain_data.link.lower()
        try:
            if not self._is_debug:
                if root_domain.startswith("http"):
                    root_domain = LinkChecker.get_root_domain(domain_data.link)[1]
                is_available, is_redemption = LinkChecker.is_domain_available_whois(root_domain)  # check whois record
                if is_available or is_redemption:
                    if is_available:
                        real_response_code = ResponseCode.Expired
                    else:
                        real_response_code = ResponseCode.MightBeExpired
                    domain_data.link = root_domain
                    domain_data.response_code = real_response_code
                #return_obj = OnSiteLink(root_domain, real_response_code, domain_data.link_level, OnSiteLink.TypeOutbound)
                    self._put_output_result_in_queue(domain_data)
            else:
                self._put_output_result_in_queue(domain_data)
        except Exception as ex:
            ErrorLogger.log_error("ExternalSiteChecker.WhoisChecker", ex, "_check_whois() " + root_domain)
        finally:
            self._add_job_done_one()

    def _check_whois_with_dns(self, page: OnSiteLink):

        real_response_code = ResponseCode.DNSError
        skip_whois_check = False
        try:
            if not self._is_debug:
                root_result = LinkChecker.get_root_domain(page.link)
                root_domain = root_result[1]
                sub_domain = root_result[4]
                suffix = root_result[5]

                if len(sub_domain) == 0 or suffix not in TldUtility.TOP_TLD_LIST:
                    skip_whois_check = True
                else:

                    if LinkChecker.is_domain_DNS_OK(sub_domain):  # check DNS first
                        real_response_code = ResponseCode.NoDNSError
                        skip_whois_check = True
                    elif not sub_domain.startswith("www."):
                        if LinkChecker.is_domain_DNS_OK("www." + root_domain):
                            real_response_code = ResponseCode.NoDNSError
                            skip_whois_check = True

                    page.response_code = real_response_code
                    page.link_type = OnSiteLink.TypeOutbound
                    page.link = root_domain
        except Exception as ex:
            ErrorLogger.log_error("WhoisChecker", ex, "_check_whois_with_dns() " + page.link)
            skip_whois_check = True
        finally:
            if not skip_whois_check and real_response_code == ResponseCode.DNSError:
                self._check_whois(page)
            else:
                self._add_job_done_one()

    def _sample_data(self):
        ref_time = time.time()
        manager, result_queue = get_queue_client(QueueManager.MachineSettingCrawler, QueueManager.Method_Whois_Input)
        if result_queue is None:
            ErrorLogger.log_error("ExternalSiteChecker.WhoisChecker._sample_data()", ValueError("result queue is None, cannot get data."))
            if not (self._stop_event.is_set() or self._internal_stop_event.is_set()):
                self._sample_data()
        else:
            while not (self._stop_event.is_set() or self._internal_stop_event.is_set()):
                data_list = []
                counter = 0
                while not result_queue.empty():

                    data = None
                    try:
                        data = result_queue.get()
                    except Exception as ex:
                        ErrorLogger.log_error("WhoisChecker._sampling_data", ex)
                        if result_queue is None:
                            manager, result_queue = get_queue_client(QueueManager.MachineSettingCrawler,
                                                                    QueueManager.Method_Whois_Input)
                    if isinstance(data, OnSiteLink):
                        counter += 1
                        data_list.append((data.link, data.response_code))
                    elif isinstance(data, tuple) and len(data) == 2:
                        #print("External Site checker: recieved:", data)
                        counter += 1
                        data_list.append(data)
                    if isinstance(data, list):
                        data_list += data
                        counter += 1
                    if counter >= self._sample_batch_size:
                        break
                    current_time = time.time()
                    if current_time - ref_time >= self._sample_batch_timeout:
                        break
                    time.sleep(self._min_sampling_duration)
                ref_time = time.time()
                if len(data_list) > 0:
                    #print("whois checker input data in db_buff: ", len(data_list))
                    self._db_buffer.append_to_buffer(data_list, convert_tuple=False)
                    data_list.clear()
                else:
                    pass
                time.sleep(self._input_period)

    def sample_gen(self):
        while not self._stop_event.is_set() or not self._internal_stop_event.is_set():
            try:
                if not self._db_buffer.reset_event.is_set():
                    for next_item in self._db_buffer:
                        time.sleep(0.0001)
                        return next_item
                print("going to next cycle in sample_gen.")
                time.sleep(1)
            except Exception as ex:
                print("sample_gen error:", ex)

    def run_farm(self):
        try:
            self._start_sending_feedback()
            input_t = threading.Thread(target=self._sample_data)
            input_t.start()  # start sampling data
            self._progress_logger.start()
            self._db_buffer.start_input_output_cycle()  # start input and output data to/from file
            pool = ThreadPool(processes=self._max_worker)
            # pool.imap_unordered(self._check_whois_with_dns, self._db_buffer, chunksize=1)
            pool.imap_unordered(self._check_whois_with_dns, iter(self.sample_gen, None), chunksize=1)
            while not self._stop_event.is_set() or not self._internal_stop_event.is_set():
                time.sleep(1)
            if self._stop_event.is_set():
                self._internal_stop_event.set()
            input_t.join()
            self._progress_logger.join()
            self._db_buffer.terminate()
            if self._stop_event.is_set():
                self._finished = True
            self._end_sending_feedback()
        except Exception as ex:
            if self._stop_event.is_set():
                self._finished = True
            ErrorLogger.log_error("ExternalSiteChecker.WhoisChecker", ex, "run_farm() index at:" + str(self._job_done))

    def get_external_count_finished(self):
        """
        ExternalTempInterface
        :return:
        """
        return self.get_job_done_count()

    def set_internal_count(self, count: int):
        """
        ExternalTempInterface
        :param count:
        :return:
        """
        self._job_done = count

    def populate_with_state(self, state):
        """
        FeedbackInterface, subclass implement this method to
        :param state: the state from previous
        :return:
        """
        if isinstance(state, WhoisCheckerState):
            self._job_done = state.progress_count
            self._db_buffer.set_progress(state.progress_count)

    def get_state(self):
        """
        FeedbackInterface, subclass this so that the controller can gather state info, which in turn will feedback into next iteration
        :return:
        """
        if self._internal_stop_event.is_set():
            return WhoisCheckerState(0, 0)
        else:
            return WhoisCheckerState(self.get_job_done_count(), self._db_buffer.get_total_record())

    def get_callback_data(self):
        """
        FeedbackInterface, subclass this so that any callback data can be gathered by the controller
        :return:
        """
        return None

    def is_programme_finshed(self):
        """
        FeedbackInterface, indicate if the programme has finished execution, if not it goes to next iteration
        :return:
        """
        return self._finished

    def is_progamme_need_restart(self):
        """
        FeedbackInterface, indicate if the programme needs to be restarted, if not it goes to next iteration
        """
        return self._internal_stop_event.is_set()

    def get_file_name(self) -> str:
        """
        ProgressLogInterface, the file name used to save in file system.
        :return:
        """
        return "whois_check_progress.csv"

    def get_column_names(self) -> []:
        """
        ProgressLogInterface, the column name for each prograss entry in get_prograss(), all in str format
        :return: array contains column names, length should match the length of prograss entries
        """
        return ["Done", "Total"]

    def reset(self):
        self._job_done = 0
        self._job_done_shadow = 0
        self._speed_penalty_count = 0

    def get_progress(self) -> []:
        """
        ProgressLogInterface, get the prograss data in tuple format, so that it can be used to complie to standard format
        :return: array contains prograss data, which has the exact length of column names in get_column_names()
        """
        total_record = self._db_buffer.get_total_record()

        if (self._job_done == self._job_done_shadow and self._job_done > 0) or (self._job_done > self._min_buff_delete_threshold * 0.9 and total_record > self._min_buff_delete_threshold):
            self._speed_penalty_count += 1
            if self._speed_penalty_count >= 2:
                ErrorLogger.log_error("WhoisChecker.get_progress()", TimeoutError("progress is stucked, restarted internal."), self._db_buffer._file_name)
                print("going to clear cache")
                self._db_buffer.clear_cache()
                self.reset()
                total_record = 0
                self._db_buffer.start_input_output_cycle()
        else:
            print("no need to clear cache.")
            self._job_done_shadow = self._job_done
            self._speed_penalty_count = 0
        return [self._job_done, total_record]

    def get_limit(self) -> int:
        """
        ProgressLogInterface, the number of samples you want to collect.
        :return: max number of samples
        """
        return self._max_sample_results