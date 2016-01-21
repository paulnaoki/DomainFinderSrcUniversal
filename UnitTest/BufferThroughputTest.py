from DomainFinderSrc.Utilities.MemoryControlProcess import MemoryControlPs
from DomainFinderSrc.Utilities.QueueManager import QueueManager, get_queue_server, get_queue_client
from DomainFinderSrc.Scrapers.SiteTempDataSrc.SiteTempDataSrcInterface import OnSiteLink, ResponseCode
from unittest import TestCase
from threading import Thread
import time
from multiprocessing.pool import ThreadPool
from multiprocessing import Process, Event
from queue import Queue
from DomainFinderSrc.Scrapers.ExternalSiteChecker import WhoisChecker
# manager, output_q = get_queue_client(QueueManager.MachineSettingCrawler, QueueManager.Method_Whois_Output)
import os


def run_queue_server():
    current_pid = os.getpid()
    print("get queue server with pid:", current_pid)
    server = get_queue_server(QueueManager.MachineSettingCrawler)
    print("queue server is started")
    server.serve_forever()


def single_input(thread_id: int, limit=1000000):
    current_pid = os.getpid()
    duration = 0.1
    link_format = "{0:d}something{1:d}.com"
    counter = 0
    batch_size = 100
    print("single input get queue:")
    manager, input_q = get_queue_client(QueueManager.MachineSettingCrawler, QueueManager.Method_Whois_Input)
    print("single input got queue:")
    while counter < limit:
        batch = list()
        for item in range(batch_size):
            batch.append((link_format.format(thread_id, counter), ResponseCode.DNSError))
            counter += 1
        try:
            input_q.put(batch)
        except Exception as ex:
            # manager.shutdown()
            print("single_input thread id:", thread_id, "with pid: ", current_pid, "error: ", ex)
            # manager, input_q = get_queue_client(QueueManager.MachineSettingCrawler, QueueManager.Method_Whois_Input)
        finally:
            counter += batch_size
            time.sleep(duration)


def single_input_process_wrapper(thread_id: int, limit=1000000):
    wrapper = Process(target=single_input, kwargs={"thread_id": thread_id, "limit": limit})
    wrapper.start()
    wrapper.join()


def single_output():
    current_pid = os.getpid()
    print("single output get queue:")
    sum_limit = 1000
    counter = 0
    manager, output_q = get_queue_client(QueueManager.MachineSettingCrawler, QueueManager.Method_Whois_Output)
    while True:
        try:
            while not output_q.empty():
                result = output_q.get()
                counter += 1
                if isinstance(result, list):
                    for item in result:
                        # print(item)
                        pass
                else:
                    # print(result)
                    pass
                if counter/sum_limit > 0 and counter % sum_limit==0:
                    print("current output count is:", counter)
                time.sleep(0.000001)
        except Exception as ex:
            print("single_output with pid: ", current_pid, " error:", ex)
            # manager, output_q = get_queue_client(QueueManager.MachineSettingCrawler, QueueManager.Method_Whois_Output)
        time.sleep(0.001)


def mass_input(worker=50):
    pool = ThreadPool(processes=worker)
    pool.imap_unordered(single_input_process_wrapper, range(worker))
    while True:
        time.sleep(1)


def whois_process(*args, **kwargs):
    checker = WhoisChecker(*args, **kwargs)
    checker.run_farm()


def checking_whois():
    # optinmal = self.max_prcess * self.concurrent_page/5
    optinmal = 260 * 3/5
    if optinmal < 10:
        worker_number = 10
    else:
        worker_number = int(optinmal)
    mem_limit = 1000
    if mem_limit < 200:
        mem_limit = 200
    stop_event = Event()
    kwargs = {"is_debug": True,
              "stop_event": stop_event,
              "max_worker": worker_number}
    whois_process_wrapper = MemoryControlPs(whois_process, func_kwargs=kwargs,
                                            mem_limit=mem_limit, external_stop_event=stop_event)
    whois_process_wrapper.start()


class Yielder:
    def __init__(self, data_len=50, laps=10):
        self.data_len = data_len
        self.laps = laps
        self.current_lap = 1

    def sample_gen(self):
        while self.current_lap <= self.laps:
            print("current lap is:", self.current_lap)
            for item in range(1, self.data_len):
                yield item
            self.current_lap += 1
            time.sleep(1)


def print_sample(obj):
    for item in obj:
        print(item)


class WhoisBufferTest(TestCase):
    # change QueueManager.Method_Whois_Output to Method_Whois_Input in single_output()
    def test_queue_server_through_put(self):
        queue_server_t = Process(target=run_queue_server)
        queue_server_t.start()
        input_t = Thread(target=mass_input, daemon=False)
        input_t.start()
        output_t = Process(target=single_output)
        output_t.start()
        input_t.join()
        output_t.join()

    # change  Method_Whois_Input in single_output() to QueueManager.Method_Whois_Output
    def testWhoisDB(self):
        queue_server_t = Process(target=run_queue_server)
        queue_server_t.start()
        input_t = Thread(target=mass_input, daemon=False)
        input_t.start()
        conversion_t = Thread(target=checking_whois)
        conversion_t.start()
        output_t = Process(target=single_output)
        output_t.start()
        input_t.join()
        output_t.join()

    def test_iter(self):
        yielder = Yielder()
        pool = ThreadPool(processes=10)
        pool.imap(func=print_sample, iterable=iter(yielder.sample_gen, None), chunksize=1)
        pool.join()

    def test_queue_init(self):
        chunk_size = 100
        queue_server_t = Process(target=run_queue_server, name="queue_server")
        queue_server_t.start()
        output_t = Process(target=single_output, name="output_thread")
        output_t.start()
        counter = 0
        for i in range(1000):
            print("init queue: ", i)
            time.sleep(0.00001)
            temp = list()
            manager, input_q = get_queue_client(QueueManager.MachineSettingCrawler, QueueManager.Method_Whois_Output)
            for j in range(chunk_size):
                temp.append(("some_domain.com{0:d}".format(counter,), 999))
                counter += 1
            input_q.put(temp)
