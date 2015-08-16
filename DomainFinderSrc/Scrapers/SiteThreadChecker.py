from multiprocessing.pool import ThreadPool
import functools
from DomainFinderSrc.Scrapers.SiteChecker import SiteChecker, ResponseCode, PageChecker
from DomainFinderSrc.Scrapers import LinkChecker
from DomainFinderSrc.Scrapers.SiteTempDataSrc.SiteTempDataDisk import *
from DomainFinderSrc.Utilities.Logging import ErrorLogger


class SiteThreadChecker(SiteChecker):
    pool_size_key = "thread_pool_size"

    def __init__(self, *args, thread_pool_size=1, **kwargs):
        #super(SiteThreadChecker, self).__init__(*args, **kwargs)
        SiteChecker.__init__(self, *args, output_buff_size=thread_pool_size*50, **kwargs)
        self.max_thread = thread_pool_size
        LinkChecker.max_http_connection = self.max_thread
        LinkChecker.max_pool_size = self.max_thread
        #self.pool = multiprocessing.Pool(processes=self.max_thread, maxtasksperchild=1)
        self.pool = ThreadPool(processes=self.max_thread)
        self._set_task_control_max(self.max_thread)
        #self.temp_queue = Queue(self.max_thread * 2)
        #self.temp_queue.put(self.page_list[0])
        #self.pump = OnSiteLinkPump(self.temp_queue, self.page_list)
        #print("init siteThreadChecker finished")

    @staticmethod
    def get_input_parameter(full_link: str, max_page:int, max_level: int, output_queue, pool_size: int):
        temp = SiteChecker.get_input_parameter_base(full_link, max_page, max_level, output_queue)
        temp.update({SiteThreadChecker.pool_size_key: pool_size})
        return temp

    def additional_reset(self):
        if self.pool is not None:
            self.pool.terminate()
            self.pool = ThreadPool(processes=self.max_thread)
            #self.pool = multiprocessing.Pool(processes=self.max_thread, maxtasksperchild=1)

    def addtional_clear(self):
        if self.pool is not None:
            self.pool.terminate()

    def stop(self):
        try:
            self.data_source.set_continue_lock(False)
            self.pool.terminate()
        except:
            pass
        super(SiteThreadChecker, self).stop()

    def begin_crawl(self, level=0):
        #while self.can_continue() and self.data_source.can_continue():
        #print("continue to work, page limit:", self.max_page, " max_level: ", self.max_level)
        #target_func = functools.partial(PageChecker.crawl_page, self)
        try:
            self.pool.imap_unordered(PageChecker.crawl_page_for_iter, self.data_source)
            while self.data_source.can_continue():
                time.sleep(0.1)
            #results = [self.pool.apply_async(PageChecker.crawl_page, args=(self, page))
            #           for page in self.data_source.get_next(OnSiteLink.TypeOnSite, ResponseCode.LinkOK)]
            #[p.get() for p in results]
        except Exception as ex:
            #self.stop()
            msg = "begin_crawl() " + str(self.get_site_info())
            ErrorLogger.log_error("SiteThreadChecker", ex, msg)



