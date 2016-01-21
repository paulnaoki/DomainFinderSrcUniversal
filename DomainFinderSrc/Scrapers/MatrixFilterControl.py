from DomainFinderSrc.Scrapers.MatrixFilter import *
from multiprocessing import Queue, Event
from DomainFinderSrc.MiniServer.Common.SocketCommands import CrawlMatrix
# from DomainFinderSrc.Scrapers.SiteTempDataSrc.DataStruct import FilteredDomainData
from DomainFinderSrc.Utilities.Logging import ErrorLogger
from DomainFinderSrc.Utilities.MemoryControlProcess import FeedbackInterface, MemoryControlPs
from DomainFinderSrc.Scrapers.SiteTempDataSrc.ExternalTempDataDiskBuffer import ExternalTempDataDiskBuffer, ExternalTempInterface
from DomainFinderSrc.Scrapers.SiteTempDataSrc.SiteTempDataSrcInterface import OnSiteLink
from DomainFinderSrc.Utilities.Proxy import *
import multiprocessing


class FilterPool(threading.Thread, FeedbackInterface):
    def __init__(self, input_queue: Queue, output_queue: Queue, queue_lock: multiprocessing.RLock, stop_event: Event,
                 matrix: CrawlMatrix, accounts=[]):
        self._input_queue = input_queue
        self._output_queue = output_queue
        self._queue_lock = queue_lock
        self._stop_event = stop_event
        self._maxtrix = matrix
        self._filters = []
        manager = AccountManager()
        self._proxies = ProxyManager().get_proxies()
        # majestic_queue = Queue()
        # archive_queue = Queue()
        if accounts is None:
            ErrorLogger.log_error("FilterPool.___init__", ValueError("accounts len is None"))
        moz_batch = 50
        moz_batch_timeout = int(moz_batch*2)

        moz_accounts = manager.get_accounts(AccountType.Moz) if len(accounts) == 0 else [x for x in accounts if x.siteType == AccountType.Moz]
        majestic_accounts = manager.get_accounts(AccountType.Majestic) if len(accounts) == 0 else [x for x in accounts if x.siteType == AccountType.Majestic]
        filter_moz = MozFilter(#input_queue=self._input_queue, output_queue=archive_queue,
                               stop_event=self._stop_event, min_DA_value=self._maxtrix.da, manager=manager,
                               accounts=moz_accounts,
                               proxies=self._proxies, batch=moz_batch, batch_get_timeout=moz_batch_timeout)  # depend on number of accounts

        workers_for_moz = len(moz_accounts)
        workers_for_archive = int(workers_for_moz/32*moz_batch)
        workers_for_majestic = int(workers_for_moz/200*moz_batch)
        # self._filters.append(filter_moz)
        # if is_majestic_filter_on:
        filter_archive = ArchiveOrgFilter(#input_queue=archive_queue, output_queue=majestic_queue,
                                          stop_event=self._stop_event, queue_lock=self._queue_lock,
                                          worker_number=workers_for_archive, en_profile_check=matrix.en_archive_check)  # min one worker
        filter_maj = MajesticFilter(#input_queue=majestic_queue, output_queue=self._output_queue,
                                    stop_event=self._stop_event, TF=self._maxtrix.tf, CF=self._maxtrix.cf,
                                    CF_TF_Deviation=self._maxtrix.tf_cf_deviation, Ref_Domains=self._maxtrix.ref_domains,
                                    manager=manager, worker_number=workers_for_majestic, en_tf_check=matrix.en_tf_check,
                                    en_spam_check=matrix.en_spam_check, accounts=majestic_accounts)  # depend on number of accounts
        if matrix.en_moz:
            self._filters.append(filter_moz)
        if matrix.archive_count:
            self._filters.append(filter_archive)
        if matrix.en_majestic:
            self._filters.append(filter_maj)
        filter_len = len(self._filters)
        if filter_len == 0:
            output_queue = input_queue  # todo:short circuit, need to test
        else:
            if filter_len > 1:
                for i in range(0, filter_len-1):
                    new_queue = Queue()
                    self._filters[i]._output_queue = new_queue
                    self._filters[i+1]._input_queue = new_queue
            self._filters[0]._input_queue = self._input_queue
            self._filters[filter_len-1]._output_queue = self._output_queue


        # else:
        #     filter_archive = ArchiveOrgFilter(input_queue=archive_queue, output_queue=self._output_queue,
        #                                       stop_event=self._stop_event, queue_lock=self._queue_lock,
        #                                       worker_number=workers_for_archive)  # min one worker
        #     self._filters.append(filter_archive)

        threading.Thread.__init__(self)

    def get_job_done(self):
        filter_len = len(self._filters)
        if filter_len > 0:
            first_filter = self._filters[0]
            if isinstance(first_filter, FilterInterface):
                return first_filter.get_job_done()
            else:
                return 0
        else:
            return 0

    def set_job_done(self, count: int):
        filter_len = len(self._filters)
        if filter_len > 0:
            last_filter = self._filters[filter_len-1]
            if isinstance(last_filter, FilterInterface):
                last_filter.set_job_done(count)

    def run(self):
        try:
            for item in self._filters:
                item.start()
            for item in self._filters:
                item.join()
        except Exception as ex:
            ErrorLogger.log_error("FilterPool", ex, "start()")


class _FilterState:
    def __init__(self, progress: int, all_data: int):
        self.progress = progress
        self.all_data = all_data


class FilterController(FeedbackInterface, ExternalTempInterface):
    """
    This Controller can be memory controlled since it implement FeedbackInterface
    """
    def __init__(self, db_ref: str, db_dir: str, input_queue: Queue, output_queue: Queue, stop_event: Event,
                 matrix: CrawlMatrix, accounts: list, force_mode=False, force_mode_offset=0, force_mode_total=0,  **kwargs):
        FeedbackInterface.__init__(self, **kwargs)
        self._stop_event = stop_event
        self._matrix = matrix
        self._db_ref = db_ref
        self._input_queue = input_queue
        self._output_queue = output_queue
        self._pool_input = Queue()
        self._pool = FilterPool(self._pool_input, self._output_queue, self._queue_lock, self._stop_event, self._matrix,
                                accounts=accounts)
        self._db_buffer = ExternalTempDataDiskBuffer(self._db_ref, self, self._stop_event, dir_path=db_dir,
                                                     buf_size=2500, output_f=5000) # control how data flow speed,
                                                     # it can keep input:output ratio = 1:1 at max 10 milion data row per hour
        #FeedbackInterface.__init__(self, **kwargs)
        ExternalTempInterface.__init__(self)
        self._populate_with_state()
        if force_mode:
            new_state = _FilterState(progress=force_mode_offset, all_data=force_mode_total)
            self.populate_with_state(new_state)

    @staticmethod
    def get_input_parameters(db_ref: str, db_dir: str, input_queue: Queue, output_queue: Queue, stop_event: Event,
                 matrix: CrawlMatrix, accounts: list, force_mode: bool, force_mode_offset:int,force_mode_total:int):
        return {"db_ref": db_ref, "db_dir": db_dir,  "input_queue": input_queue, "output_queue": output_queue, "stop_event": stop_event,
                 "matrix": matrix, "accounts": accounts,
                 "force_mode": force_mode, "force_mode_offset": force_mode_offset, "force_mode_total": force_mode_total,}

    def _sample_data_buffer_input(self):
        while not self._stop_event.is_set():
            data_list = []
            # if isinstance(self._queue_lock, multiprocessing.RLock):
            while not self._input_queue.empty():
                #with self._queue_lock:
                data = self._input_queue.get()
                if isinstance(data, tuple) and len(data) == 2:
                    data_list.append(data)
            if len(data_list) > 0:
                self._db_buffer.append_to_buffer(data_list, convert_tuple=False)
                data_list.clear()
            time.sleep(1)

    def _sample_data_buffer_output(self):
        for item in self._db_buffer:
            if self._stop_event.is_set():
                break
            if isinstance(item, OnSiteLink):
                self._pool_input.put(FilteredDomainData(domain=item.link, found=int(time.time())))

    def begin_filtering(self):
        self._start_sending_feedback()
        self._db_buffer.start_input_output_cycle()  # start input and output data to/from file
        input_t = threading.Thread(target=self._sample_data_buffer_input)
        output_t = threading.Thread(target=self._sample_data_buffer_output)
        input_t.start()  # start sampling data
        output_t.start()
        self._pool.start()
        if self._pool.is_alive():
            self._pool.join()
        self._db_buffer.terminate()
        if input_t.is_alive():
            input_t.join()
        if output_t.is_alive():
            output_t.join()
        self._end_sending_feedback()

    def populate_with_state(self, state):
        """
        FeedbackInterface, subclass implement this method to
        :param state: the state from previous
        :return:
        """
        if isinstance(state, _FilterState):
            self._pool.set_job_done(state.progress)
            self._db_buffer.set_progress(state.progress)

    def get_state(self):
        """
        FeedbackInterface, subclass this so that the controller can gather state info, which in turn will feedback into next iteration
        :return:
        """
        return _FilterState(progress=self._pool.get_job_done(), all_data=self._db_buffer.get_total_record())

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
        return self._stop_event.is_set()

    def get_external_count_finished(self) -> int:
        """
        ExternalTempInterface, get the number of job done in ExternalTempDataDiskBuffer
        :return:
        """
        return self._pool.get_job_done()

    def set_internal_count(self, count: int):
        """
        ExternalTempInterface, set the number of job done in ExternalTempDataDiskBuffer
        :param count:
        :return:
        """
        self._pool.set_job_done(count)

