from threading import Thread
from DomainFinderSrc.Utilities.QueueManager import get_queue_server
from unittest import TestCase
from DomainFinderSrc.Scrapers.SiteThreadChecker import SiteThreadChecker
from DomainFinderSrc.Scrapers.SiteChecker import PageChecker, OnSiteLink
from DomainFinderSrc.Scrapers.LinkChecker import LinkChecker
from DomainFinderSrc.Utilities.QueueManager import QueueManager, get_queue_server, get_queue_client
import time
from multiprocessing import Process, Event


def run_queue_server():
    server = get_queue_server(QueueManager.MachineSettingCrawler)
    print("queue server is started")
    server.serve_forever()


def single_output(stop_event: Event):
    print("single output get queue:")
    sum_limit = 1000
    counter = 0
    manager, output_q = get_queue_client(QueueManager.MachineSettingCrawler, QueueManager.Method_Whois_Input)
    while not stop_event.is_set():
        try:
            while not output_q.empty() or not stop_event.is_set():
                result = output_q.get(False, 1)
                counter += 1
                if isinstance(result, list):
                    for item in result:
                        print("server queue output:", str(item), "count:", counter)
                else:
                    # print(result)
                    pass
                if counter/sum_limit > 0 and counter % sum_limit==0:
                    print("current output count is:", counter)
                time.sleep(0.000001)
        except Exception as ex:
            pass
            # manager, output_q = get_queue_client(QueueManager.MachineSettingCrawler, QueueManager.Method_Whois_Output)
        finally:
            print("going to sleep.")
            time.sleep(1)


class SiteCheckerTest(TestCase):
    def testThreadChecker(self):
        stop_event = Event()
        link = "munichre.com"
        checker = SiteThreadChecker(full_link=link, thread_pool_size=3, max_page=3000, max_level=10)

        def crawl():
            checker.crawling()

        queue_server_t = Process(target=run_queue_server)
        queue_server_t.start()
        output_t = Process(target=single_output, args=(stop_event,))
        output_t.start()
        # link = "http://sweetlifebake.com/#axzz3t4Nx7b7N"
        crawl_t = Thread(target=crawl)
        crawl_t.start()
        timeout = 1000
        counter = 0
        while counter < timeout:
            time.sleep(1)
            counter += 1
        print("is going to sudden death.")
        stop_event.set()
        checker.sudden_death()
        if crawl_t.is_alive():
            crawl_t.join()
        output_t.terminate()
        queue_server_t.terminate()

        print("finished")


    def testPageCrawl(self):
        link = "http://www.secondcityhockey.com"
        checker = SiteThreadChecker(full_link=link, thread_pool_size=2, max_page=1000, max_level=10)
        checker.agent = "VegeBot-Careful"
        page = OnSiteLink(link=link, response_code=999)
        next_page = OnSiteLink(link="http://www.secondcityhockey.com/2014/10/9/6951991/state-of-the-blog-lets-party-and-be-nice-and-hip-and-cool/in/6645018", response_code=999)
        # next_page = OnSiteLink(link="http://www.secondcityhockey.com/2014/", response_code=999)

        # PageChecker.check_internal_page(checker, page)
        internal, external = PageChecker.check_internal_page(checker, next_page)
        print("external links:")
        for item in external:
            print(item)
        print("internal links:")
        for item in internal:
            print(item)

    def testPageCrawl2(self):
        link = "http://stackoverflow.com/"
        checker = SiteThreadChecker(full_link=link, thread_pool_size=2, max_page=1000, max_level=10)
        checker.agent = "VegeBot-Careful"
        page = OnSiteLink(link=link, response_code=999)
        next_page = OnSiteLink(link="http://stackoverflow.com/questions/5836674/why-does-debug-false-setting-make-my-django-static-files-access-fail", response_code=999)
        PageChecker.check_internal_page(checker, page)
        internal, external = PageChecker.check_internal_page(checker, next_page)
        print("external links:")
        for item in external:
            print(item)
        print("internal links:")
        for item in internal:
            print(item)
