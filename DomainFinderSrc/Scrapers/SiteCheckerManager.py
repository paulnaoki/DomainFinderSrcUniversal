import threading
from threading import Thread, _RLock
from queue import Queue
import time
from tornado.ioloop import IOLoop
from DomainFinderSrc.Scrapers.SiteSimpleChecker import SiteSimpleChecker
from DomainFinderSrc.Scrapers.LinkChecker import LinkChecker
from DomainFinderSrc.Scrapers.SiteChecker import SiteCheckerController
from DomainFinderSrc.Utilities.ThreadFlag import threadFlag
import multiprocessing
from DomainFinderSrc.Utilities.QueueManager import *


class SiteCheckerManager(Thread, SiteCheckerController):
    def __init__(self, job_name: str, site_list: [], max_thread=10, page_max_level=10, max_page_per_site=1000,
                 output_delegate=None):
        Thread.__init__(self)
        self.name = job_name
        if max_thread <= 0:
            max_thread = 10
        self.max_thread = max_thread
        LinkChecker.max_pool_size = max_thread
        LinkChecker.max_http_connection = max_thread
        self.inputQueue = Queue()
        self.outputQueue = Queue()
        self.input_lock = threading.Lock()
        self.output_lock = threading.Lock()
        self.input_thread_stop_flag = threadFlag()
        self.output_thread_stop_flag = threadFlag()
        self.all_stop = threadFlag()
        self.inputThreads = []
        self.tempList = site_list # if there is a need to add new sites during scripting, add to this list
        self.threadPrfix = "Thread-"
        self.page_max_level = page_max_level
        self.max_page_per_site = max_page_per_site
        self.output_delegate = output_delegate # delegate of type f(x:OnSiteLink)
        self._stop_event = threading.Event()
        #self.tread_count = 0
        self.finished = False
        for i in range(1, max_thread+1):
            threadName = self.threadPrfix + str(i)
            self.inputThreads.append(inputThread(i, threadName, self.input_thread_stop_flag, self.inputQueue,
                                                 self.outputQueue, self.input_lock, self.output_lock,
                                                 page_max_level= self.page_max_level,
                                                 max_page_per_site=self.max_page_per_site))
        self.output_thread = outputThread(0, self.threadPrfix+"Output", self._stop_event,  self.outputQueue,
                                          self.output_lock, self.output_delegate)

    def run(self):
        if self.add_jobs_to_queue(self.tempList):
            self.tempList.clear()
            self.output_thread.start()

            for t in self.inputThreads:
                t.start()
            while True:
                if not self.inputQueue.empty():
                    time.sleep(0.5)
                else:
                    self.input_thread_stop_flag.flag = True
                    break

            for t in self.inputThreads:
                t.join()
            self.output_thread_stop_flag.flag = True
            self.output_thread.join()
            self.finished = True
            return True
        else:
            return False

    def add_page_done(self, number_page_done: int):
        pass

    def site_finished(self):
        pass

    def add_jobs_to_queue(self, site_list: []):
        """
        Add a list of site(str)
        :param site_list: a list of site in str
        :return: True if successful, else False
        """
        if not self.finished and site_list is not None and len(site_list) > 0:
            self.input_lock.acquire()
            #for item in site_list:
            self.inputQueue.queue.extend(site_list)
            self.input_lock.release()
            return True
        else:
            return False


class inputThread(Thread):
    def __init__(self, threadID, name: str, flag: threadFlag, inputQ: Queue, outputQ: Queue,
                 input_queueLock:_RLock, output_queueLock:_RLock,
                 page_max_level=10, max_page_per_site=1000):
        Thread.__init__(self)
        self.threadID = threadID
        self.inputQ = inputQ
        self.outputQ = outputQ
        self.name = name
        self.flagStop = flag
        self.input_queueLock = input_queueLock
        self.output_queueLock = output_queueLock
        self.finished = False
        self.page_max_level = page_max_level
        self.max_page_per_site = max_page_per_site
        self.io_loop = IOLoop.current(False)

    def run(self):
        print("starting " + self.name)
        self.process_data_input()
        if self.io_loop is not None:
            self.io_loop.close()
        print("Exiting " + self.name)

    def process_data_input(self):
        while not self.flagStop.is_flag_set():
            time.sleep(1)
            self.input_queueLock.acquire()
            if not self.inputQ.empty():
                site = self.inputQ.get()
                print(self.name + " -> " + site)
                self.input_queueLock.release()
                checker = SiteSimpleChecker(site, self, site_level=0, max_level=self.page_max_level,
                                      max_page=self.max_page_per_site, delegate=self.send_data, io_loop=self.io_loop)
                checker.begin_crawl()
                #result = "%s processing %s" % (self.name, data)
                #self.send_data(result)
            else:
                self.input_queueLock.release()

    def send_data(self, data: str):
        self.output_queueLock.acquire()
        if not self.outputQ.full():
            self.outputQ.put(data)
            self.output_queueLock.release()
        else:
            self.output_queueLock.release()


class outputThread(Thread):
    def __init__(self, threadID, name: str, stop_event: multiprocessing.Event, inputQ, delegate=None):
        Thread.__init__(self)
        self.threadID = threadID
        #manager, result_queue = get_queue_client(QueueManager.MachineSettingCrawler, QueueManager.Method_Whois_Input)
        self.inputQ = inputQ
        self.name = name
        self.stop_event = stop_event
        #self.queueLock = queueLock
        self.delegate = delegate

    def run(self):
        print("starting " + self.name)
        self.process_data_output()
        print("Exiting " + self.name)

    def process_data_output(self):
        while not self.stop_event.is_set():
            self.consume_data()
            time.sleep(0.1)

    def consume_data(self):
        if not self.inputQ.empty():
            #with self.queueLock:
            data = self.inputQ.get()
            if self.delegate is None:
                print(data)
            else:
                self.delegate(data)

