from multiprocessing import Queue, Event
from multiprocessing.pool import ThreadPool
import threading
import random
import multiprocessing

from DomainFinderSrc.MozCom import *

from DomainFinderSrc.MajesticCom import *
from DomainFinderSrc.Utilities import FilePath, FileIO
from DomainFinderSrc.SiteConst import *
from DomainFinderSrc.Scrapers.SiteTempDataSrc.DataStruct import FilteredDomainData
from DomainFinderSrc.Utilities.Logging import ErrorLogger, PrintLogger, CsvLogger
import DomainFinderSrc
from DomainFinderSrc.ArchiveOrg.ProfileExtract import ArchiveOrg
from DomainFinderSrc.Scrapers.TLDs import TldUtility
import collections


class FilterInterface(threading.Thread):
    def __init__(self, stop_event: Event, input_queue: Queue=None, output_queue: Queue=None, worker_number: int=1,
                 queue_lock: multiprocessing.RLock=None, throughput_debug=False, batch=1, batch_get_timeout=60, **kwargs):
        self._input_queue = input_queue
        self._output_queue = output_queue
        self._stop_event = stop_event
        if worker_number <= 0:
            worker_number = 1
            ErrorLogger.log_error("FilterInterface", ValueError("worker number is 0, reset to 1"), "__init__")
        self._worker_number = worker_number
        self._process_queue_lock = queue_lock
        self._is_throughput_debug = throughput_debug
        self._sync_lock = threading.RLock()
        self._job_done = 0
        self._batch = batch
        self._batch_get_timeout = batch_get_timeout
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

    def process_data_batch(self, data: collections.Iterable, **kwargs) -> []:
        return [self.process_data(x, **kwargs) for x in data]

    def _func_wrap_batch(self, data):
        if isinstance(data, collections.Iterable):
            formatted_input = [self.format_input(x) for x in data]
            kwargs = self.get_input_kwargs()
            if kwargs is None:
                processed = self.process_data_batch(data=formatted_input)
            else:
                processed = self.process_data_batch(data=formatted_input, **kwargs)
            if isinstance(processed, collections.Iterable):
                formatted_output = [self.format_output(x) for x in processed]
                for item in formatted_output:
                    self._output_queue.put(item)
        else:
            return

    def _func_wrap(self, data):
        if data is None:
            return
        formatted_input = self.format_input(data)
        kwargs = self.get_input_kwargs()
        if kwargs is None:
            processed = self.process_data(data=formatted_input)
        else:
            processed = self.process_data(data=formatted_input, **kwargs)
        if processed is not None:
            formatted_output = self.format_output(processed)
            self._output_queue.put(formatted_output)

    def _forerver_get_batch(self) -> list:
        counter = 0
        batch = list()
        current_time = time.time()
        while not self._stop_event.is_set():
            if not self._input_queue.empty():
                item = self._input_queue.get()
                if item is not None:
                    batch.append(item)
                    counter += 1
                if counter >= self._batch:
                    return batch
            lapse = int(time.time() - current_time)
            if lapse >= self._batch_get_timeout and len(batch) > 0:
                return batch
            else:
                time.sleep(0.0001)

    def _forever_get(self):
        while not self._stop_event.is_set():
            if not self._input_queue.empty():
                item = self._input_queue.get()
                if item is not None:
                    return item
            else:
                time.sleep(0.0001)

    def run(self):
        pool = ThreadPool(processes=self._worker_number)
        if self._batch > 1:
            pool.imap_unordered(func=self._func_wrap_batch, iterable=iter(self._forerver_get_batch, None))
        else:
            pool.imap_unordered(func=self._func_wrap, iterable=iter(self._forever_get, None))
        while not self._stop_event.is_set():
            time.sleep(0.01)


class ArchiveOrgFilter(FilterInterface):
    """
    Get the number of useful archives
    """
    def __init__(self, min_profile=1, min_page_size=1, en_profile_check=True, *args, **kwargs):
        self._min_profile = min_profile
        self._min_page_size = min_page_size
        self._en_profile_check = en_profile_check
        self._log_file = "Archive_count_filtering.csv"
        FilterInterface.__init__(self, *args, **kwargs)

    def get_input_kwargs(self):
        return None

    def process_data(self, data: FilteredDomainData, **kwargs):
        result_ok = False
        if isinstance(data, FilteredDomainData):
            try:
                if len(data.domain_var) == 0:
                    data.domain_var = data.domain
                links = ArchiveOrg.get_url_info(data.domain_var, min_size=self._min_page_size, limit=-100)
                count = len(links)
                data.archive = count
                if count < self._min_profile:
                    pass
                    # raise ValueError("profile count is less than:" + str(self._min_profile))
                result_ok = True
            except Exception as ex:
                if not self._is_throughput_debug:
                    pass
                    # ErrorLogger.log_error("ArchiveOrgFilter.process_data()", ex, data.domain_var)
            finally:
                with self._sync_lock:
                    self._job_done += 1
                        #with self._process_queue_lock:
                    if result_ok:
                        if not self._is_throughput_debug:
                            CsvLogger.log_to_file(self._log_file, [(data.domain, data.da, data.archive)]) # log this to file
                        self._output_queue.put(data)
                        # return data
                    else:
                        if self._is_throughput_debug:
                            self._output_queue.put(data)
                        # return None
        else:
            return None
            # return None


class MozFilter(FilterInterface):
    """
    Get DA about a Domain
    """
    def __init__(self, *args, min_DA_value=5, manager: AccountManager, accounts=[], batch=50, batch_get_timeout=120, proxies=None, **kwargs):
        acc_manager = manager
        self._min_DA_value = min_DA_value
        if len(accounts) == 0:
            self._account_list = acc_manager.get_accounts(AccountType.Moz)
        else:
            self._account_list = [x for x in accounts if isinstance(x, SiteAccount)]
        self._proxies = proxies
        self._log_file = "Moz_filtering.csv"
        if proxies is not None and len(proxies) > 0:
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

        self._max_wait = 120
        self._min_sleep_time = 45
        assert self._max_wait >= self._min_sleep_time, "max rate for moz api is 10s per request"
        FilterInterface.__init__(self, *args, worker_number=len(self._account_list), batch=batch, batch_get_timeout=batch_get_timeout, **kwargs)

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
            time.sleep(0.0001)
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
                    if not self._is_throughput_debug:
                        ranking = moz.get_ranking_data(data.domain)
                    else:
                        ranking = 100
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
                    if not self._is_throughput_debug:
                        CsvLogger.log_to_file(self._log_file, [(data.domain, data.da)]) # log this to file
                    self._output_queue.put(data)

    def process_data_batch(self, data: collections.Iterable, **kwargs):
        #print("MozFilter processing: ", data)
        account = kwargs.get("Account")
        temp = []
        try:
            if isinstance(data, collections.Iterable) and isinstance(account, SiteAccount):
                temp = [x for x in data if isinstance(x, FilteredDomainData) and TldUtility.is_top_tld(x.domain)]
                check_list = [y.domain for y in temp]
                sleep_time =random.randint(self._min_sleep_time, self._max_wait)
                time.sleep(sleep_time)
                moz = MozCom(account)
                if not self._is_throughput_debug:
                    rankings = moz.get_ranking_data_batch(check_list, limit=len(check_list))
                else:
                    rankings = [100] * len(temp)
                for i in range(len(temp)):
                    temp[i].da = rankings[i]
            else:
                raise ValueError("account is none in process_data_batch()")
        except Exception as ex:
            ErrorLogger.log_error("MozFilter", ex, "process_data_batch() " + str(data) + " account: " + account.userID)
        finally:
            PrintLogger.print("Moz processed: " + str(data) + " with: " + account.userID)
            with self._sync_lock:
                job_done = [x for x in data if x is not None]
                self._job_done += len(job_done)
                if account is not None:
                    account.Available = True
                for item in temp:
                    if isinstance(item, FilteredDomainData):
                        # print("moz processed:", item.domain)
                        if item.da >= self._min_DA_value:
                            if not self._is_throughput_debug:
                                CsvLogger.log_to_file(self._log_file, [(item.domain, item.da)]) # log this to file
                            self._output_queue.put(item)


class MajesticSpamException(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


class MajesticFilter(FilterInterface):
    """
    Get TF, CF of a domain
    """
    def __init__(self, *args, TF=15, CF=15, CF_TF_Deviation=0.80, Ref_Domains=10, manager: AccountManager,
                 accounts=[], en_tf_check=True, en_spam_check=True, **kwargs):
        self._min_tf = TF
        self._min_cf = CF
        self._min_ref_domains = Ref_Domains
        acc_manager = manager
        self._cf_tf_deviation = CF_TF_Deviation
        self._majestic_result_anchor_limit = 50
        self._majestic_result_ref_domain_limit = 50
        self._max_backlink_to_ref_domain_ratio = 6.0
        self._max_percentage_for_anchor_text_ratio = 0.1
        self._en_spam_check = en_spam_check
        self._en_tf_check = en_tf_check
        self._log_file = "Majestic_filtering_good.csv"
        self._bad_log_file = "Majestic_filtering_bad.csv"
        self._spam_keyword = [x.lower() for x in FileIO.FileHandler.read_lines_from_file(FilePath.get_spam_filter_keywords_file_path())]
        self._spam_anchor = [x.lower() for x in FileIO.FileHandler.read_lines_from_file(FilePath.get_spam_filter_anchors_file_path())]
        self._white_keyword_list = [x.lower() for x in FileIO.FileHandler.read_lines_from_file(FilePath.get_spam_filter_white_list_file_path())]
        self._bad_country = [x.upper() for x in FileIO.FileHandler.read_lines_from_file(FilePath.get_spam_filter_bad_country_path())]
        if len(accounts) == 0:
            self._account_list = acc_manager.get_accounts(AccountType.Majestic)
        else:
            self._account_list = [x for x in accounts if isinstance(x, SiteAccount)]
        worker_number = kwargs["worker_number"]
        if worker_number <= 0:
            worker_number = len(self._account_list)
        kwargs.update({"worker_number": worker_number})
        FilterInterface.__init__(self, *args, **kwargs)

    def get_input_kwargs(self) -> dict:
        account = None
        while True:
            available_accs = None
            with self._sync_lock:
                available_accs = self._account_list
                # available_accs = [x for x in self._account_list if x.Available]
                if len(available_accs) > 0:
                    account_num = random.randint(0, len(available_accs)-1)
                    account = available_accs[account_num]
                    account.Available = False
                    break
            time.sleep(0.0001)
        return {"Account": account}

    def _filter_tf_cf_backlink_ratio(self, majestic: MajesticCom, data: FilteredDomainData) -> FilteredDomainData:
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
                        item_cf_tf_ratio1 = abs(1-item.cf/item.tf)
                        item_cf_tf_ratio2 = abs(1-item.tf/item.cf)
                        item_deviation = min([item_cf_tf_ratio1, item_cf_tf_ratio2])
                    else:
                        continue
                    if data.tf > 0:
                        data_cf_tf_ratio1 = abs(1-data.cf/data.tf)
                        data_cf_tf_ratio2 = abs(1-data.tf/data.cf)
                        data_deviation = min([data_cf_tf_ratio1, data_cf_tf_ratio2])
                        # data_deviation = abs(1-data_cf_tf_ratio)

                    if item.tf >= self._min_tf  and item.cf >=self._min_cf and item_deviation < data_deviation and item_deviation <= self._cf_tf_deviation:
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

    def _filter_domain_name(self, domain: str) -> bool:
        for keyword in self._spam_keyword:
            if keyword in domain and not any(x in domain for x in self._white_keyword_list):
                raise MajesticSpamException("domain name {0:s} has spam word {1:s}".format(domain, keyword))
        return True

    def _filter_anchor_text(self, majestic: MajesticCom, domain: str) -> bool:
        """
        check anchor text.
        :param majestic:
        :param domain:
        :return:True if everything ok, else raise Exception.
        """
        brand = LinkChecker.get_root_domain(domain)[6]
        min_anchor_variation_limit = 2
        no_follow_limit = 0.5
        non_brand_share_limit = 0.25
        domain_contain_limit = 5
        is_in_anchor = False
        brand_name_repeat_count = 0
        brand_name_backlinks_count = 0
        anchor_list, total_backlinks, deleted, nofollow, total_ref_domains \
            = majestic.get_anchor_text_info(domain=domain, max_count=self._majestic_result_anchor_limit,
                                            is_dev=DomainFinderSrc.IS_DEBUG, fresh_data=True)
        if len(anchor_list) <= min_anchor_variation_limit:
            raise MajesticSpamException("number of anchor variation is less than 2.")
        elif nofollow/total_backlinks > no_follow_limit:
            pass
            # raise MajesticSpamException("nofollow backlinks are more than 50%.")
        elif len(self._spam_anchor) > 0:
            count = 0
            for anchor, ref_domains, total_links, deleted_links, no_follow_links in anchor_list:
                if brand in anchor or brand in anchor.replace(' ', ''):
                    if count < domain_contain_limit:
                        is_in_anchor = True
                    brand_name_backlinks_count += total_links
                    brand_name_repeat_count += 1
                elif ref_domains/total_ref_domains > non_brand_share_limit:
                # elif total_links/total_backlinks > non_brand_share_limit:
                    raise MajesticSpamException("non branded anchor '{0:s}' exceeded limit {1:.2f}.".format(anchor, ref_domains/total_ref_domains))

                for spam in self._spam_anchor:
                    if spam in anchor and not any(x in anchor for x in self._white_keyword_list):
                        raise MajesticSpamException("anchor {0:s} is in spam word {1:s}".format(anchor, spam))
                count += 1
            # if brand_name_backlinks_count/total > self._max_percentage_for_anchor_text_ratio:
            #     raise MajesticSpamException("domain name mentioned in achor texts more than {0:.1f}.".format(self._max_percentage_for_anchor_text_ratio*100,))
        if not is_in_anchor:
            pass
            #print(anchor_list)
            # raise MajesticSpamException("anchor does not have the domain name in top {0:d} results.".format(domain_contain_limit,))

        return True

    def _filter_ref_domains(self, majestic: MajesticCom, domain: str) -> bool:
        """
        check ref_domain info,
        :param majestic:
        :param domain:
        :return: True if everything is ok, else raise Exception.
        """
        max_bad_country_ratio = 0.25
        bad_country_count = 0
        max_bad_country_count = 5
        max_backlinks_for_single_bad_country = 30
        ref_domains = majestic.get_ref_domains(domain, max_count=self._majestic_result_ref_domain_limit,
                                               is_dev=DomainFinderSrc.IS_DEBUG, fresh_data=True)
        total_record = len(ref_domains)
        for ref_domain in ref_domains:
            if isinstance(ref_domain, MajesticRefDomainStruct):
                if ref_domain.country in self._bad_country:
                    bad_country_count += 1
                    if ref_domain.backlinks > max_backlinks_for_single_bad_country:
                        raise MajesticSpamException("{0:s} from bad country has more than {1:d} backlinks.".format(ref_domain.domain,max_backlinks_for_single_bad_country))
        if bad_country_count >= max_bad_country_count:
            raise MajesticSpamException("too many bad countries, {0:d} detected.".format(bad_country_count,))
        bad_country_ratio = bad_country_count/total_record
        if total_record > 0 and bad_country_ratio > max_bad_country_ratio:
            raise MajesticSpamException("bad country ratio in ref domains is too high: {0:.1f} percent.".format(bad_country_ratio*100,))
        return True

    def process_data(self, data: FilteredDomainData, **kwargs):
        account = kwargs.get("Account")
        # is_domain_good = False
        is_spammed = False
        try:
            if isinstance(data, FilteredDomainData) and isinstance(account, SiteAccount):
                majestic = MajesticCom(account)
                if self._en_spam_check:
                    self._filter_domain_name(domain=data.domain)
                    # self._filter_anchor_text(majestic, data.domain)
                    # self._filter_ref_domains(majestic, data.domain)
                if self._en_tf_check:
                    data = self._filter_tf_cf_backlink_ratio(majestic, data)
                if not (data.tf >= self._min_tf and data.ref_domains >= self._min_ref_domains):
                    raise ValueError("tf or cf doesn't match. tf:" + str(data.tf) + " cf: " + str(data.cf) + " ref domain: " + str(data.ref_domains))
                # if data.backlinks / data.ref_domains > self._max_backlink_to_ref_domain_ratio:
                #     raise MajesticSpamException("backlink to ref domain ratio is greater than {0:.1f}".format(self._max_backlink_to_ref_domain_ratio,))
                if self._en_spam_check:
                    self._filter_anchor_text(majestic, data.domain)
                    self._filter_ref_domains(majestic, data.domain)
                # is_domain_good = True
            else:
                raise ValueError("account is none in process_data")
        except MajesticSpamException as mjx_ex:
            is_spammed = True
            data.exception = str(mjx_ex)
        except Exception as ex:
            data.exception = str(ex)
            # ErrorLogger.log_error("MajesticFilter.process_data()", ex, str(data))
        finally:
            PrintLogger.print("Majestic processed: '" + str(data) + "' with: " + account.userID)
            if isinstance(data, FilteredDomainData):
                with self._sync_lock:
                    self._job_done += 1
                    if account is not None:
                        account.Available = True
                    # if data.cf >= self._min_cf and data.tf >= self._min_tf:
                    if data.tf >= self._min_tf and data.cf >= self._min_cf and data.ref_domains >= self._min_ref_domains:
                    # if data.tf >= self._min_tf and data.ref_domains >= self._min_ref_domains:
                        #print("Majatic output:", data)
                        # PrintLogger.print("domain: " + data.domain + " is good.")
                        if not self._is_throughput_debug:
                            if is_spammed:
                                CsvLogger.log_to_file(self._bad_log_file, [data.to_tuple()], dir_path=FilePath.get_temp_db_dir())
                            else:
                                CsvLogger.log_to_file(self._log_file, [data.to_tuple()], dir_path=FilePath.get_temp_db_dir()) # log this to file
                        self._output_queue.put(data)
                        return data
                    # elif is_spammed:
                    #     if not self._is_throughput_debug:
                    #         CsvLogger.log_to_file(self._bad_log_file, [data.to_tuple()], dir_path=FilePath.get_temp_db_dir())
                    #     self._output_queue.put(data)
                        # return data
                    else:
                        if self._is_throughput_debug:
                            self._output_queue.put(data)
                        # return None
                        # print("domain: " + data.domain + " has exception:" + data.exception)
            else:
                pass
                # return None


