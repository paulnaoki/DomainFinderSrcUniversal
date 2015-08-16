from DomainFinderSrc.MozCom import *
from DomainFinderSrc.MajesticCom import *
from DomainFinderSrc.Utilities import FilePath, FileIO
from multiprocessing import Queue, Event
from multiprocessing.pool import ThreadPool
import threading
from DomainFinderSrc.SiteConst import *
import random
from DomainFinderSrc.Scrapers.SiteTempDataSrc.DataStruct import FilteredDomainData
from DomainFinderSrc.Utilities.Logging import ErrorLogger, PrintLogger, CsvLogger
import DomainFinderSrc
from DomainFinderSrc.ArchiveOrg.ProfileExtract import ArchiveStruct, ArchiveOrg
from DomainFinderSrc.Scrapers.TLDs import TldUtility
import multiprocessing


class FilterInterface(threading.Thread):
    def __init__(self, input_queue: Queue, output_queue: Queue,  stop_event: Event, worker_number: int, queue_lock: multiprocessing.RLock=None):
        self._input_queue = input_queue
        self._output_queue = output_queue
        self._stop_event = stop_event
        self._worker_number = worker_number
        self._process_queue_lock = queue_lock
        self._sync_lock = threading.RLock()
        if worker_number == 0:
            ErrorLogger.log_error("FilterInterface", ValueError("worker number is 0"), "__init__")
        self._job_done = 0
        threading.Thread.__init__(self)

    @staticmethod
    def format_input(data):
        if isinstance(data, FilteredDomainData):
            return data
        elif isinstance(data, tuple) and len(data) == 2:
            return FilteredDomainData(domain=data[0])

    @staticmethod
    def format_output(data):
        return data

    def get_job_done(self):
        return self._job_done

    def set_job_done(self, count: int):
        self._job_done = count

    def get_input_kwargs(self) -> dict:
        raise NotImplementedError

    def process_data(self, data, **kwargs) -> object:
        raise NotImplementedError

    def _func_wrap(self, data):
        if data is None:
            return
        formatted_input = self.format_input(data)
        kwargs = self.get_input_kwargs()
        if kwargs is None:
            processed = self.process_data(data=formatted_input)
        else:
            processed = self.process_data(data=formatted_input, **kwargs)
        formatted_output = self.format_output(processed)
        self._output_queue.put(formatted_output)

    def _forever_get(self):
        while not self._stop_event.is_set():
            if not self._input_queue.empty():
                item = self._input_queue.get()
                if item is not None:
                    return item
            else:
                time.sleep(0.01)

    def run(self):
        pool = ThreadPool(processes=self._worker_number)
        pool.imap_unordered(func=self._func_wrap, iterable=iter(self._forever_get, None))
        while not self._stop_event.is_set():
            time.sleep(1)


class ArchiveOrgFilter(FilterInterface):
    """
    Get the number of useful archives
    """
    def __init__(self, *args, **kwargs):
        FilterInterface.__init__(self, *args, worker_number=1, **kwargs)

    def get_input_kwargs(self):
        return None

    def process_data(self, data: FilteredDomainData, **kwargs):
        if isinstance(data, FilteredDomainData):
            try:
                if len(data.domain_var) == 0:
                    data.domain_var = data.domain
                links, count = ArchiveOrg.get_url_info(data.domain_var, min_size=1)
                data.archive = count
            except Exception as ex:
                ErrorLogger.log_error("ArchiveOrgFilter.process_data()", ex, data.domain_var)
            finally:
                with self._sync_lock:
                    self._job_done += 1
                        #with self._process_queue_lock:
                    self._output_queue.put(data)
        else:
            pass


class MozFilter(FilterInterface):
    """
    Get DA about a Domain
    """
    def __init__(self, *args, min_DA_value=5, manager: AccountManager, proxies=None,  **kwargs):
        acc_manager = manager
        self._min_DA_value = min_DA_value
        self._account_list = acc_manager.get_accounts(AccountType.Moz)
        self._proxies = proxies
        self._log_file = "Moz_filtering.csv"
        if proxies is not None:
            counter = 0
            if len(proxies) >= len(self._account_list):
                for account in self._account_list:
                    account.proxy = proxies[counter]
                    counter += 1
            else:
                for proxy in self._proxies:
                    self._account_list[counter].proxy = proxy
                    counter += 1
                self._account_list = self._account_list[0: len(self._proxies) - 1]

        self._max_wait = 150
        self._min_sleep_time = 30
        assert self._max_wait >= self._min_sleep_time, "max rate for moz api is 10s per request"
        FilterInterface.__init__(self, *args, worker_number=len(self._account_list), **kwargs)

    def get_input_kwargs(self) -> dict:
        account = None
        while True:
            available_accs = None
            with self._sync_lock:
                available_accs = [x for x in self._account_list if x.Available]
                if len(available_accs) > 0:
                    account_num = random.randint(0, len(available_accs)-1)
                    account = available_accs[account_num]
                    if isinstance(account, SiteAccount):
                        account.Available = False
                        # proxy_count = len(self._proxies)
                        # if proxy_count > 0:
                        #     proxy_num = random.randint(0, proxy_count - 1)
                        #     proxy = self._proxies[proxy_num]
                        #     account.proxy = proxy
                    break
            time.sleep(1)
        return {"Account": account}

    def process_data(self, data: FilteredDomainData, **kwargs):
        #print("MozFilter processing: ", data)
        account = kwargs.get("Account")
        try:
            if isinstance(data, FilteredDomainData) and isinstance(account, SiteAccount):
                if TldUtility.is_top_tld(data.domain):
                    sleep_time =random.randint(self._min_sleep_time, self._max_wait)
                    time.sleep(sleep_time)
                    moz = MozCom(account)
                    ranking = moz.get_ranking_data(data.domain)
                    data.da = ranking
                else:
                    pass
            else:
                raise ValueError("account is none in process_data")
        except Exception as ex:
            ErrorLogger.log_error("MozFilter", ex, "process_data() " + str(data) + " account: " + account.userID)
        finally:
            PrintLogger.print("Moz processed: " + str(data) + " with: " + account.userID)
            if isinstance(data, FilteredDomainData):
                with self._sync_lock:
                    self._job_done += 1
                    if account is not None:
                        account.Available = True
                if data.da >= self._min_DA_value:
                    CsvLogger.log_to_file(self._log_file, [(data.domain, data.da)]) # log this to file
                    self._output_queue.put(data)


class MajesticFilter(FilterInterface):
    """
    Get TF, CF of a domain
    """
    def __init__(self, *args, TF=15, CF=15, CF_TF_Deviation=0.44, Ref_Domains=10, manager: AccountManager, **kwargs):
        self._min_tf = TF
        self._min_cf = CF
        self._min_ref_domains = Ref_Domains
        acc_manager = manager
        self._cf_tf_deviation = CF_TF_Deviation
        self._majestic_result_anchor_limit = 100
        self._majestic_result_ref_domain_limit = 100
        self._log_file = "Majestic_filtering.csv"
        self._spam_keyword = [x.lower() for x in FileIO.FileHandler.read_lines_from_file(FilePath.get_spam_filter_keywords_file_path())]
        self._spam_anchor = [x.lower() for x in FileIO.FileHandler.read_lines_from_file(FilePath.get_spam_filter_anchors_file_path())]
        self._bad_country = [x.upper() for x in FileIO.FileHandler.read_lines_from_file(FilePath.get_spam_filter_bad_country_path())]
        self._account_list = acc_manager.get_accounts(AccountType.Majestic)
        FilterInterface.__init__(self, *args, worker_number=len(self._account_list), **kwargs)

    def get_input_kwargs(self) -> dict:
        account = None
        while True:
            available_accs = None
            with self._sync_lock:
                available_accs = [x for x in self._account_list if x.Available]
                if len(available_accs) > 0:
                    account_num = random.randint(0, len(available_accs)-1)
                    account = available_accs[account_num]
                    account.Available = False
                    break
            time.sleep(1)
        return {"Account": account}

    def _filter_tf_cf(self, majestic: MajesticCom, data: FilteredDomainData) -> FilteredDomainData:
        ranking = majestic.get_cf_tf_list(["http://"+data.domain,
                                           "www."+data.domain,
                                           "http://www."+data.domain],
                                          is_dev=DomainFinderSrc.IS_DEBUG)
        if ranking is not None and len(ranking) > 0:
            current_tf = 0
            for item in ranking:
                if isinstance(item, MajesticComStruct):
                    item_cf_tf_ratio = 999
                    data_cf_tf_ratio = 999
                    item_deviation = 999
                    data_deviation = 999
                    if item.tf > 0:
                        item_cf_tf_ratio = item.cf/item.tf
                        item_deviation = abs(1-item_cf_tf_ratio)
                    else:
                        continue
                    if data.tf > 0:
                        data_cf_tf_ratio = data.cf/data.tf
                        data_deviation = abs(1-data_cf_tf_ratio)

                    if item.tf >= self._min_tf and item_deviation < data_deviation and item_deviation <= self._cf_tf_deviation:
                        data.domain_var = item.domain
                        data.tf = item.tf
                        data.cf = item.cf
                        data.backlinks = item.backlinks
                        data.ref_domains = item.ref_domains
                        data.topic = item.topic
        return data

    @staticmethod
    def _is_valid_ISO8859_1_str(original_str: str) -> bool:
        try:
            temp = original_str.encode(encoding='iso-8859-1').decode(encoding='iso-8859-1')
            if temp == original_str:
                return True
            else:
                return False
        except:
            return False

    def _filter_anchor_text(self, majestic: MajesticCom, domain: str) -> bool:
        min_anchor_variation_limit = 2
        no_follow_limit = 0.5
        domain_contain_limit = 5
        is_in_anchor = False
        anchor_list, total, deleted, nofollow \
            = majestic.get_anchor_text_info(domain=domain, max_count=self._majestic_result_anchor_limit,
                                            is_dev=DomainFinderSrc.IS_DEBUG)
        if len(anchor_list) <= min_anchor_variation_limit:
            raise ValueError("number of anchor variation is less than 2.")
        elif (deleted + nofollow)/total > no_follow_limit:
            raise ValueError("deleted and nofollow backlinks are more than 50%.")
        elif len(self._spam_anchor) > 0:
            count = 0
            for anchor in anchor_list:
                if domain in anchor:
                    is_in_anchor = True
                if count >= domain_contain_limit and not is_in_anchor:
                    raise ValueError("anchor does not have the domain name in top {0:d} results.".format(domain_contain_limit,))

                # if not MajesticFilter._is_valid_ISO8859_1_str(anchor):
                #     raise ValueError("anchor contains invalid western language word: {0:s}.".format(anchor,))
                for spam in self._spam_anchor:
                    if anchor in spam:
                        raise ValueError("anchor {0:s} is in spam word {1:s}".format(anchor, spam))
            count += 1

        return True

    def _filter_ref_domains(self, majestic: MajesticCom, domain: str) -> bool:
        max_bad_country_ratio = 0.1
        bad_country_count = 0
        ref_domains = majestic.get_ref_domains(domain, max_count=self._majestic_result_ref_domain_limit,
                                               is_dev=DomainFinderSrc.IS_DEBUG)
        total_record = len(ref_domains)
        for ref_domain in ref_domains:
            if isinstance(ref_domain, MajesticRefDomainStruct):
                if ref_domain.country in self._bad_country:
                    bad_country_count += 1

        bad_country_ratio = bad_country_count/total_record > max_bad_country_ratio
        if total_record > 0 and bad_country_ratio:
            raise ValueError("bad country ratio is too high: {0:s} percent.", bad_country_ratio)
        return True

    def process_data(self, data: FilteredDomainData, **kwargs):
        account = kwargs.get("Account")
        try:
            if isinstance(data, FilteredDomainData) and isinstance(account, SiteAccount):
                majestic = MajesticCom(account)
                data = self._filter_tf_cf(majestic, data)
            else:
                raise ValueError("account is none in process_data")
        except Exception as ex:
            ErrorLogger.log_error("MozFilter", ex, "process_data() " + str(data))
        finally:
            PrintLogger.print("Majestic processed: " + str(data) + " with: " + account.userID)
            if isinstance(data, FilteredDomainData):
                with self._sync_lock:
                    self._job_done += 1
                    if account is not None:
                        account.Available = True
                # if data.cf >= self._min_cf and data.tf >= self._min_tf:
                if data.tf >= self._min_tf and data.ref_domains >= self._min_ref_domains:
                    #print("Majatic output:", data)
                    CsvLogger.log_to_file(self._log_file, [(data.domain, data.da, data.tf, data.cf)]) # log this to file
                    self._output_queue.put(data)


