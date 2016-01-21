from urllib.parse import urlsplit
from urllib import robotparser
from reppy.parser import Rules
from DomainFinderSrc.Scrapers.SiteTempDataSrc.SiteTempDataSrcInterface import *
import bs4
from DomainFinderSrc.Scrapers.LinkChecker import ResponseCode, LinkChecker
from DomainFinderSrc.Scrapers.SiteTempDataSrc.SiteTempDataSrcInterface import OnSiteLink, SiteInfo
from DomainFinderSrc.Scrapers.SiteTempDataSrc.SiteTempDataDiskWithBuffer import SiteTempDataDiskWithBuff
from DomainFinderSrc.MiniServer.Common.SocketCommands import SeedSiteFeedback
from DomainFinderSrc.Utilities.MemoryControlProcess import FeedbackInterface
from DomainFinderSrc.Utilities.Logging import *
from multiprocessing import Event
from requests import Response
from DomainFinderSrc.Utilities.FilePath import *
from DomainFinderSrc.Scrapers.SiteTempDataSrc.ExternalTempDataDiskBuffer import \
    ExternalTempDataDiskBuffer, ExternalTempInterface
import os
import multiprocessing
from DomainFinderSrc.Utilities.QueueManager import *
from collections import deque


class SiteCheckerState:
    def __init__(self, page_count: int, page_need_look_up: int, internal_page_count: int,
                 external_page_count: int, current_level: int,
                 datasource_index: int, datasource_output_c: int, datasource_ref: str,
                 log_started_time: int, log_sample_index: int):
        self.page_count = page_count
        self.page_need_look_up = page_need_look_up
        self.internal_page_count = internal_page_count
        self.external_page_count = external_page_count
        self.current_level = current_level
        self.datasource_index = datasource_index
        self.datasource_ref = datasource_ref
        self.datasource_output_c = datasource_output_c
        self.log_started_time = log_started_time
        self.log_sample_index = log_sample_index


class SiteFeedback:
    def __init__(self, new_page_done, finished, seed_feedback, datasource_ref: str=""):
        self.page_done = new_page_done
        self.finished = finished
        self.seed_feedback = seed_feedback
        self.datasource_ref = datasource_ref


class SiteCheckerController:
    def add_page_done(self, number_page_done: int):
        pass

    def site_finished(self):
        pass

    def can_continue(self):
        return True


class SiteChecker(FeedbackInterface, SiteTempDataSrcRefInterface, ProgressLogInterface, ExternalTempInterface):
    full_link_key = "full_link"
    datasource_key = "data_source"
    controller_ley = "controller"
    max_level_key = "max_level"
    max_page_key = "max_page"
    output_queue_key = "output_queue"

    _use_lxml_parser = False

    def __init__(self, full_link: str="", data_source: SiteTempDataSrcInterface=None,
                 controller: SiteCheckerController=None,
                 max_level=10, max_page=1000, delegate=None, output_buff_size=2000,
                 output_queue=None, output_all_external=False, result_delegate=None,
                 memory_control_terminate_event=None, check_robot_text=True,
                 **kwargs):
        """
        :param full_link: The full link of a domain, e.g: https://www.google.co.uk
        :param domain: domain to crawl
        :param max_level: stop crawling if it reaches this level
        :param max_page: maximum pages to check within a site, also stop crawling
        :param delegate: if this is not None, then it will send the latest result of external domain of ResponseCode==404 or 999
        :param result_delegate: send site_info upon finish
        :param memory_control_terminate_event: if this is not None and being set, it will be able to terminate an external memory controlled process.
        :return:
        """
        FeedbackInterface.__init__(self, **kwargs)
        #super(SiteChecker, self).__init__(**kwargs)
        if full_link is None or len(full_link) == 0:
            raise ValueError()

        original_path = ""
        try:
            paras = urlsplit(full_link)
            self.scheme, self.domain, original_path = paras[0], paras[1], paras[2]
        except:
            pass

        domain_data = LinkChecker.get_root_domain(full_link, False)
        self.root_domain = domain_data[1]
        self.sub_domain = domain_data[4]
        self.domain_suffix = domain_data[5]
        self.sub_domain_no_local = self.sub_domain.strip(self.domain_suffix)
        if self.scheme == "":
            self.scheme = "http"
        if self.domain == "":
            self.domain = self.root_domain
        self.orginal_link = full_link
        self.domain_link = LinkChecker.get_valid_link(self.root_domain, full_link, self.scheme)
        self.max_level = max_level
        self.max_page = max_page
        self.page_count = 0  # keep track page done
        self._page_count_shadow = 0 # track previous count
        self._all_page_count_shadow = 0 #track previous count in datasource
        self.internal_page_count = 0
        self.internal_page_last_count = 0
        self.page_allocated = 0
        self.current_level = 0  # if this = 0, it is root domain/home_page
        self._stop_event = Event()
        valid_file_name = SiteTempDataSrcInterface.get_valid_file_name(self.domain_link)
        self._external_db_buffer = ExternalTempDataDiskBuffer(valid_file_name+".ext.db", self,
                                                              stop_event=self._stop_event,
                                                              buf_size=int(output_buff_size/2),
                                                              dir_path=get_db_buffer_default_dir(),
                                                              convert_output=False)
        self._external_db_buffer.append_to_buffer([(self.root_domain, ResponseCode.DNSError),], convert_tuple=False)
        self._memory_control_terminate_event = memory_control_terminate_event
        self.task_control_lock = threading.RLock()
        if data_source is None:
            #self.data_source = SiteTempDataDisk(self.root_domain, ref_obj=self)
            self.data_source = SiteTempDataDiskWithBuff(ref=self.domain_link, output_buff_size=output_buff_size, ref_obj=self)
        else:
            self.data_source = data_source  # a list of OnSiteLink
        self.delegate = delegate
        if LinkChecker.might_be_link_html_page(original_path):
            self.data_source.append(OnSiteLink(self.domain_link, response_code=ResponseCode.LinkOK, link_level=1)) # add the root domain as a starting point
        self.data_source.append(OnSiteLink(self.scheme + "://www."+self.sub_domain, ResponseCode.LinkOK, link_level=1))
        self.data_source.append(OnSiteLink(self.scheme + "://" + self.domain, ResponseCode.LinkOK, link_level=1))
        self.cache_list = []  # internal page cache
        self.page_need_look_up_temp = 0
        self.cache_list.append(self.domain_link)
        if "www." not in self.sub_domain:
            self.cache_list.append(self.scheme + "://www."+self.sub_domain)
        self.cache_list.append(self.scheme + "://" + self.domain)
        self.page_need_look_up = self.data_source.count_all()
        self.cache_size = 500  # create a small cache list to avoid going to check link in file system with lots of read and write
        self._double_check_cache_lock = threading.RLock()
        self._double_check_cache = deque(maxlen=self.cache_size)
        self.external_cache_list = []
        self.external_cache_size = 500  # cache that hold external sites
        self.external_links_checked = 0
        self.add_internal_page_OK_only = True
        self.output_queue = output_queue
        self.output_all_external = output_all_external
        self.controller = controller
        self.result_delegate = result_delegate
        self.page_count_lock = threading.RLock()
        self.internal_page_count_lock = threading.RLock()
        self.level_lock = threading.RLock()
        self.page_look_up_lock = threading.RLock()
        self.external_link_check_lock = threading.RLock()
        self._finihsed = False
        self.task_control_max = 1
        self.agent = "VegeBot (we follow your robots.txt settings before crawling, you can slow down the bot by change the Crawl-Delay parameter in the settings." \
                     "if you have an enquiry, please email to: abuse-report@terrykyleseoagency.com)"
        self.agent_from = "abuse-report@terrykyleseoagency.com"
        if check_robot_text:
            self.robot_agent = LinkChecker.get_robot_agent(self.sub_domain, protocol=self.scheme)
        else:
            self.robot_agent = None
        self.site_crawl_delay = 0.60

        if isinstance(self.robot_agent, Rules):
            delay_temp = self.robot_agent.delay(self.agent)
            if delay_temp is not None and delay_temp != self.site_crawl_delay:
                self.site_crawl_delay = delay_temp

        self.task_control_counter = 1
        self._speed_penalty_count = 0
        self._speed_penalty_threshold = 10
        self._progress_logging_speed = 120
        self._output_period = 120
        self._output_batch_size = 100
        self._death_wish_sent = False
        SiteChecker._is_lxml_parser_exist()
        self._output_thread = None
        self._output_queue = None
        self.progress_logger = ProgressLogger(self._progress_logging_speed, self, self._stop_event)
        self._status = "Start"
        self._populate_with_state()  # restore laste known state
        # self.data_source.additional_startup_procedures()  # use the data set in self._populate_with_state() to start

    # def _empty_external_links_db(self):
    #     if self.output_queue is not None:
    def _put_result_in_output_queue_loop(self, item_list: list):
        if not self._stop_event.is_set():
            try:
                self._output_queue.put(item_list, True, 2)
            except Exception as ex:
                if self._output_queue is None:
                    manager, self._output_queue = get_queue_client(QueueManager.MachineSettingCrawler,
                                                             QueueManager.Method_Whois_Input)
                time.sleep(0.1)
                ErrorLogger.log_error("SiteChecker._get_external_links_to_queue", self.sub_domain+" "+str(ex))
                self._put_result_in_output_queue_loop(item_list)

    def _get_external_links_to_queue(self):
        ref_time = time.time()
        manager, self._output_queue = get_queue_client(QueueManager.MachineSettingCrawler, QueueManager.Method_Whois_Input)
        self.output_queue = self._output_queue  # override output_queue
        # if result_queue is None:
        #     ErrorLogger.log_error("SiteChecker._get_external_links_to_queue()", ValueError("result queue is none, cannot put item in queue."))
        # else:
        batch = list()
        counter = 0
        for item in self._external_db_buffer:
            if self._stop_event.is_set() or self.external_links_checked >= self._external_db_buffer.count_all():
                try:
                    manager.shutdown()
                except:
                    pass
                finally:
                    # print("exist _get_external_links_to_queue")
            # if self._stop_event.is_set() and self.external_links_checked >= self._external_db_buffer.count_all():
                    break
            elif isinstance(item, tuple):
                # print("outputting item: ", str(item))
                batch.append((item[0], item[1]))
                counter += 1
            if len(batch) > 0:
                current_time = time.time()
                if current_time - ref_time or len(batch) >= self._output_batch_size:
                    self._put_result_in_output_queue_loop(batch)
                    self.external_links_checked += len(batch)
                    ref_time = time.time()
                    batch.clear()

            time.sleep(0.0001)

    @staticmethod
    def _is_lxml_parser_exist():
        try:
            import lxml

        except ImportError:
            SiteChecker._use_lxml_parser = False
        else:
            SiteChecker._use_lxml_parser = True

    def use_lxml_parser(self):
        return SiteChecker._use_lxml_parser

    @staticmethod
    def get_input_parameter_base(full_link: str, max_page: int, max_level: int, output_queue) -> dict:
        return {SiteChecker.full_link_key: full_link, SiteChecker.max_page_key: max_page,
                SiteChecker.max_level_key: max_level, SiteChecker.output_queue_key: output_queue}

    def get_external_count_finished(self) -> int:
        """
        ExternalTempInterface, get the number of job done in ExternalTempDataDiskBuffer
        :return:
        """
        return self.external_links_checked

    def set_internal_count(self, count: int):
        """
        ExternalTempInterface, set the number of job done in ExternalTempDataDiskBuffer
        :param count:
        :return:
        """
        self.external_links_checked = count

    def _set_task_control_max(self, concurrent_task: int):
        if concurrent_task <= 0:
            raise ValueError
        self.task_control_max = concurrent_task
        self.task_control_counter = concurrent_task
        min_page_per_s = concurrent_task/20
        self._speed_penalty_threshold = self._progress_logging_speed * min_page_per_s
        if self.site_crawl_delay > 1/min_page_per_s:
            ErrorLogger.log_error("SiteChecker._set_task_control_max()",
                                  ValueError("site has crawl delay greater than mas delay."), self.domain_link)
            self._status = "Stopped"
            self.sudden_death()

    def get_site_feedback(self) -> SeedSiteFeedback:
        return SeedSiteFeedback(self.orginal_link, page_count=self.get_page_need_look_up())

    def get_site_info(self) -> SiteInfo:  # keep the original reference when sending back the site infomation
        info = SiteInfo(self.orginal_link, self.data_source)
        return info

    def populate_with_state(self, state):
        if state is not None and isinstance(state, SiteCheckerState):
            self._status = "Restarted"
            self.page_count = state.page_count
            self.page_allocated = state.page_count
            self.internal_page_count = state.internal_page_count
            self.internal_page_last_count = state.internal_page_count
            self.external_links_checked = state.external_page_count
            self._external_db_buffer.set_progress(state.external_page_count)
            self.page_need_look_up = state.page_need_look_up
            self.current_level = state.current_level
            self.progress_logger.set_reference(state.log_sample_index, state.log_started_time)
            counter = 0
            if self.data_source is not None:
                try:
                    for item in self.data_source.get_next():
                        if counter >= self.cache_size:
                            break
                        if isinstance(item, OnSiteLink) and not LinkChecker.is_external_link(self.root_domain, item.link):
                            self.cache_list.append(item.link)
                            # print("--restore: ", item)
                            counter += 1
                except Exception as ex:
                    msg = "error in SiteChecker.populate_with_state(), trying to populate cache, " + self.root_domain
                    ErrorLogger.log_error("SiteChecker", ex, msg)

                self.data_source.ref = state.datasource_ref
                self.data_source.output_c = state.datasource_output_c
                self.data_source.set_progress(state.datasource_index if state.datasource_index < state.page_count else state.page_count)
                self.data_source.set_continue_lock(True)

    def get_file_name(self):
        return self.data_source.ref

    def get_limit(self):
        return 100000

    def get_column_names(self):
        return ["Page Index", "External", "All", "Status"]

    def get_progress(self):
        data_source_count = self.data_source.count_all()
        if self.page_count - self._page_count_shadow <= self._speed_penalty_threshold:  # determine if site is slow
            self._speed_penalty_count += 1
            if self._speed_penalty_count > 2:
                self._status = "Stopped"
                self.sudden_death()
        else:
            self._speed_penalty_count = 0

        if self.page_count == self._page_count_shadow and data_source_count == self._all_page_count_shadow:  # determine if site is stucked
            self._status = "Stopped"
            self.sudden_death()

        self._page_count_shadow = self.page_count
        self._all_page_count_shadow = data_source_count
        return [self.page_count, self.external_links_checked, data_source_count, self._status]

    def is_programme_finshed(self):
        return self._finihsed

    def get_callback_data(self):
        with self.page_count_lock:
            gap = self.internal_page_count - self.internal_page_last_count
            self.internal_page_last_count = self.internal_page_count
            seed_feedback = None
            if self._finihsed:
                seed_feedback = self.get_site_feedback()

        return SiteFeedback(gap, self._finihsed, seed_feedback=seed_feedback, datasource_ref=self.data_source.ref)

    def get_state(self):
        return SiteCheckerState(page_count=self.page_count, page_need_look_up=self.page_need_look_up,
                                current_level=self.current_level, internal_page_count=self.internal_page_count,
                                external_page_count= self.external_links_checked,
                                datasource_index=self.data_source.temp_counter,
                                datasource_output_c=self.data_source.output_c,
                                datasource_ref=self.data_source.ref, log_started_time=self.progress_logger.begin_time,
                                log_sample_index=self.progress_logger.limit_counter,)

    def additional_reset(self):
        pass

    def addtional_clear(self):
        pass

    def stop(self):
        # natural stop
        self._status = "Stopped"
        self.progress_logger.report_progress()
        self._stop_event.set()
        if self.progress_logger.is_alive():
            self.progress_logger.join()

    def clear(self):
        self.cache_list.clear()
        self.addtional_clear()

    def acquire_task(self, level: int, link: str):
        tasked_acquired = True
        if link.endswith('/'):
            temp = link
        else:
            temp = link + '/'
        with self.task_control_lock:
            if len(self._double_check_cache) > 0:
                if temp in self._double_check_cache:
                    print("duplicate link found:", link)
                    tasked_acquired = False
                else:
                    if len(self._double_check_cache) >= self.cache_size:
                        self._double_check_cache.popleft()
                    self._double_check_cache.append(temp)
            self.task_control_counter -= 1
            self.page_allocated += 1
            if tasked_acquired:
                if level > self.current_level:
                    self.current_level = level
            # time.sleep(self.site_crawl_delay)
        return tasked_acquired

    def release_task(self, new_page: int):
        with self.task_control_lock:
            if self.page_need_look_up == 1 and new_page == 0:
                PrintLogger.print("set to stop data source")
                self.data_source.set_continue_lock(False)
            else:
                self.page_count += 1
                self.page_need_look_up += new_page
                #self.external_links_checked += external_page_count
                self.task_control_counter += 1
                # was determine if it is internal or external page
                self.internal_page_count += 1
                if self.internal_page_count > self.max_page or self.current_level > self.max_level:
                    if self.data_source.can_continue():
                        PrintLogger.print("set stop: " + str(self.internal_page_count)+" level: "+str(self.current_level))
                        self.data_source.set_continue_lock(False)

    def get_page_count(self):
        with self.page_count_lock:
            page_count = self.page_count
        return page_count

    def set_page_count(self, page_count: int):
        with self.page_count_lock:
            self.page_count = page_count

    def set_internal_page_count(self, count: int):
        with self.internal_page_count_lock:
            self.internal_page_count += count

    def get_internal_page_count(self):
        with self.internal_page_count_lock:
            count = self.internal_page_count
        return count

    def get_current_level(self):
        with self.level_lock:
            current_level = self.current_level
        return current_level

    def set_current_level(self, level):
        with self.level_lock:
            self.current_level = level

    def get_page_need_look_up(self):
        with self.page_look_up_lock:
            page_look_up = self.page_need_look_up
        #self.page_look_up_lock.release()
        return page_look_up

    def set_page_need_look_up(self, page_count):
        with self.page_look_up_lock:
            #time.sleep(0.1)
            self.page_need_look_up = page_count
        # self.page_look_up_lock.release()

    def set_page_need_look_up_plus_more(self, count: int):
        with self.page_look_up_lock:
            self.page_need_look_up += count

    def get_internal_page_progress_index(self)->int:
        return self.get_page_count()

    def set_internal_page_progress_index(self, index: int):
        self.page_count = index
        self.page_allocated = index

    def is_idle(self):
        idle = False
        with self.task_control_lock:
            page_need_look_up = self.get_page_need_look_up()
            new_task_added = page_need_look_up - self.page_need_look_up_temp
            has_new_task = True if new_task_added > 0 else False
            #page_count = self.get_page_count()
            if has_new_task:
                self.page_need_look_up_temp = page_need_look_up
            else:
                if self.task_control_counter >= self.task_control_max:
                    idle = True
                #     print("is idle")
                # else:
                #     print("is working")
        return idle

    def add_link_to_cache(self, link):
        if len(self.cache_list) > self.cache_size:
            return
        else:
            if link.endswith('/'):
                self.cache_list.append(link)
            else:
                self.cache_list.append(link+'/')

    def is_link_in_cache(self, link):
        if link.endswith('/'):
            temp = link
        else:
            temp = link + '/'
        return True if temp in self.cache_list else False

    def reset_as(self, domain: str, link: str=""):  # reset the target domain
        PrintLogger.print("crawl reset as: "+domain)
        self.domain = domain
        self.domain_link = self.scheme + "://" + self.domain
        self.page_count = 0
        self.current_level = 0
        self.set_page_need_look_up(1)
       # self.set_page_looked_up(0)
        self.clear()
        if len(link) == 0:
            self.cache_list.append(self.domain_link)
            self.data_source.re_target(self.domain_link, OnSiteLink(self.domain_link, response_code=ResponseCode.LinkOK, link_level=1))
            #self.data_source.append(OnSiteLink(self.domain_link, response_code=ResponseCode.LinkOK, link_level=1))
        else:
            self.cache_list.append(link)
            self.data_source.re_target(link, OnSiteLink(link, response_code=ResponseCode.LinkOK, link_level=1))
            #self.data_source.append(OnSiteLink(link, response_code=ResponseCode.LinkOK, link_level=1))
        self.additional_reset()
        self.data_source.additional_startup_procedures()

    def crawling(self):  # call this method to start operation
        self._start_sending_feedback()
        self._output_thread = threading.Thread(target=self._get_external_links_to_queue)
        if self.data_source.can_continue():
            self.data_source.additional_startup_procedures()  # use the data set in self._populate_with_state() to start
            self._external_db_buffer.start_input_output_cycle()
            self._output_thread.start()
            self.progress_logger.start()
            self.progress_logger.report_progress()  # log first row
            self._status = "Work"
            self.begin_crawl()
            # prefix = "www."
            # page_count_limit = 2
            # if self.page_count <= page_count_limit and prefix not in self.domain_link:
            #     new_domain = prefix + self.sub_domain
            #     self.reset_as(new_domain)
            #     self._status = "Work"
            #     self.begin_crawl()
            # print("going to stop all.")
            self.stop()
            self.clear()

            self.data_source.additional_finish_procedures()
            # print("going to finish output buffer.")
            self._external_db_buffer.terminate()
            # print("going to stop output_thread.")
            if self._output_thread.is_alive():
                self._output_thread.join()
        PrintLogger.print("finished naturally: "+self.domain_link)
        # print("finished naturally.")
        self._finihsed = True
            #calling this at the end of operation
        PrintLogger.print("send last response")
        # print("send last response")
        # print("send last response.")
        self._end_sending_feedback()
        if self._memory_control_terminate_event is not None:
            self._memory_control_terminate_event.set()

    def sudden_death(self):
        if not self._finihsed:
            self._finihsed = True
            PrintLogger.print("start sudden death: "+self.orginal_link)
            #self.stop()
            self.stop()

            self.clear()
            self.data_source.set_continue_lock(False)
            self.data_source.additional_finish_procedures()
            self._external_db_buffer.terminate()
            if isinstance(self._output_thread, threading.Thread):
                if self._output_thread.is_alive():
                    self._output_thread.join()
                #calling this at the end of operation
            PrintLogger.print("send last response")
            self._end_sending_feedback()
            if self._memory_control_terminate_event is not None:
                ErrorLogger.log_error("SiteChecker", TimeoutError("slow processing speed, terminated."), self.orginal_link)
                self._memory_control_terminate_event.set()

    def begin_crawl(self, level=0):  # subclass this to make different behaviour
        pass


class PageChecker:

    @staticmethod
    def is_link_in_list(link: str, data: []) -> True:
        try:
            found = next((x for x in data if x.link == link), None)
            return True if found is not None else False
        except:
            return False
        # if data is not None and len(data) > 0:
        #     found = next((x for x in data if x.link == link), None)
        #     return True if found is not None else False
        # else:
        #     return False

    @staticmethod
    def check_external_page(checker: SiteChecker, page: OnSiteLink, timeout=10):
        """
        check DNS Error Only
        :param checker:
        :param page:
        :param timeout:
        :return:
        """
        # response = LinkChecker.get_response(page.link, timeout)
        #real_response_code = response[0]
        #real_response_code = ResponseCode.LinkOK

        #print("-------checking external " + page.link)
        try:
            root_result = LinkChecker.get_root_domain(page.link)
            root_domain = root_result[1]
            sub_domain = root_result[4]

            if len(sub_domain) == 0 or root_domain in checker.external_cache_list:
                return
            else:
                if len(checker.external_cache_list) < checker.external_cache_size:
                    checker.external_cache_list.append(root_domain)

            real_response_code = page.response_code
            if LinkChecker.is_domain_DNS_OK(sub_domain):  # check DNS first
                real_response_code = ResponseCode.NoDNSError
            elif not sub_domain.startswith("www."):
                if LinkChecker.is_domain_DNS_OK("www." + root_domain):
                    real_response_code = ResponseCode.NoDNSError
                # response = LinkChecker.get_response(page.link, timeout)  # check 404 error

            page.response_code = real_response_code
            page.link_type = OnSiteLink.TypeOutbound
            page.link = root_domain
            #print(" ready to output external:", str(page))
            if checker.output_all_external or ResponseCode.domain_might_be_expired(real_response_code):
                    # if checker.delegate is not None:
                    #     checker.delegate(new_page)
                if checker.output_queue is not None:
                    with checker._queue_lock:
                        checker.output_queue.put(page)
        except Exception as ex:
            PrintLogger.print(ex)
            ErrorLogger.log_error("PageChecker", ex, "check_external_page() " + page.link)

    @staticmethod
    def check_internal_page(checker: SiteChecker, page: OnSiteLink, timeout=10) -> ([], []):
        internal_pages = []
        external_pages = []
        #
        # if isinstance(checker.robot_agent, robotparser.RobotFileParser):
        #     if not checker.robot_agent.can_fetch(useragent=checker.agent, url=page.link):
        #         return [], []
        # print("checking internal_page", page)

        if isinstance(checker.robot_agent, Rules):
            try:
                if not checker.robot_agent.allowed(page.link, agent=checker.agent):
                    return [], []
            except:
                return [], []

        use_lxml_parser = checker.use_lxml_parser()
        with checker.task_control_lock:
            time.sleep(checker.site_crawl_delay)
            response = LinkChecker.get_page_source(page.link, timeout, agent=checker.agent, from_src=checker.agent_from)
        if response is None or response.status_code == ResponseCode.LinkError:
            return [], []
        paras = urlsplit(page.link)
        page_scheme, page_domain = paras[0], paras[1]

        links = LinkChecker.get_webpage_links_from_source(response, use_lxml_parser)

        for link in links:
            link_type = OnSiteLink.TypeOutbound
            valid_link = LinkChecker.get_valid_link(page_domain, link.strip(), page_scheme)
            # if PageChecker.is_link_in_list(valid_link, new_pages):
            #     continue
            try:
                link_paras = urlsplit(valid_link)
                link_scheme, link_domain, link_path = link_paras[0], link_paras[1], link_paras[2]
                if link_domain.lower().startswith("mailto:"):
                    continue
                if not LinkChecker.might_be_link_html_page(link_path):
                    continue
            except:
                continue
            # if str(link_domain).endswith(checker.root_domain):
            if checker.sub_domain_no_local in link_domain:  # important change
                if checker.data_source.all_record > checker.max_page:
                    continue
                link_type = OnSiteLink.TypeOnSite
            else: # external
                valid_link = link_scheme + "://" + link_domain
            if link_type == OnSiteLink.TypeOnSite:
                if checker.is_link_in_cache(valid_link):
                    continue
                else:
                    checker.add_link_to_cache(valid_link)
                    internal_page = (valid_link, ResponseCode.LinkOK, page.link_level+1, OnSiteLink.TypeOnSite)
                    internal_pages.append(internal_page)
            else:
                stripped = str(link_domain).lower().strip()
                if stripped in checker.external_cache_list:
                    continue
                if len(checker.external_cache_list) < checker.external_cache_size:
                    checker.external_cache_list.append(stripped)
                external_page = (stripped, ResponseCode.DNSError)
                external_pages.append(external_page)
        return internal_pages, external_pages

    @staticmethod
    def crawl_page(checker: SiteChecker, page: OnSiteLink, timeout=10):  # update self.page_list
            new_page_counter = 0
            external_count = 0
            #is_external = True if page.link_type == OnSiteLink.TypeOutbound else False
            try:
                # print("checking:", page.link)
                if checker.acquire_task(page.link_level, page.link):
                   # print(root_domain, " len:", len(root_domain), " origional: ", checker.root_domain, " len:", len(checker.root_domain))
                    #if not is_external:  # exeternal domain
                    # page_count = checker.page_allocated
                    # print(page_count, " ", page.link)
                    pages, external_page = PageChecker.check_internal_page(checker, page, timeout)
                    new_page_counter = len(pages)
                    if new_page_counter > 0:
                        checker.data_source.append_many(pages, False)
                    external_count = len(external_page)
                    if external_count > 0:
                        checker._external_db_buffer.append_to_buffer(external_page, convert_tuple=False)
                    # else:
                    #     PageChecker.check_external_page(checker, page, timeout)
            except Exception as ex:
                PrintLogger.print(ex)
                msg = "crawl_page(): " + str(checker.page_allocated) + " " + str(page)
                ErrorLogger.log_error("PageChecker", ex, msg)
            finally:
                checker.release_task(new_page_counter)
                # page_count = checker.page_allocated
                # print(page_count, " ", page.link)

    # @staticmethod
    # def crawl_page_for_iter(checker: SiteChecker, page: OnSiteLink):
    #         PageChecker.crawl_page(checker, page=page)

    @staticmethod
    def crawl_page_for_iter(obj: tuple):
        if obj is not None and len(obj) >= 2 and isinstance(obj[0], SiteChecker):
            PageChecker.crawl_page(obj[0], obj[1])
        else:
            print("invalid input argument for crawl_page_for_iter", obj)