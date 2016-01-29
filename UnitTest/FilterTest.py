from unittest import TestCase
from DomainFinderSrc.Scrapers.MatrixFilter import *
from DomainFinderSrc.Scrapers.MatrixFilterControl import *
from multiprocessing import Event, RLock
import queue
import csv
from UnitTest.Accounts import moz_account, majestic_account
from DomainFinderSrc.MiniServer.Common.DBInterface import FilteredResultDB
from DomainFinderSrc.Scrapers.SiteTempDataSrc.DataStruct import FilteredDomainData
from DomainFinderSrc.Utilities.TimeIt import timeit
import threading
import csv


def get_archive_filter(**input_param) -> ArchiveOrgFilter:
    archive_filter = ArchiveOrgFilter(**input_param)
    return archive_filter


def get_majestic_filter(**input_param) -> MajesticFilter:
        manager = AccountManager()
        manager.AccountList.append(majestic_account)
        # input_param ={"input_queue": queue.Queue(), "output_queue": queue.Queue(), "stop_event": Event()}
        majestic_filter = MajesticFilter(manager=manager, **input_param)
        return majestic_filter


def get_moz_filter(**input_param) -> MozFilter:
    # db_path = "/Users/superCat/Desktop/PycharmProjectPortable/sync/"
    # manager = AccountManager()
    moz_filter = MozFilter(**input_param)
    return moz_filter


def testThroughPut(fil, manager=None, accounts=[], test_sites_count=5000):
        manager = AccountManager()
        input_q = queue.Queue()
        output_q = queue.Queue()

        stop_event = Event()
        input_param ={"input_queue": input_q, "output_queue": output_q, "stop_event": stop_event,
                      "throughput_debug": True,
                      "manager": manager,
                      "accounts": accounts}

        test_filter = fil(**input_param)
        test_filter.start()
        site_count = test_sites_count
        count = 0

        def input_thread():
            data_path = "/Users/superCat/Desktop/PycharmProjectPortable/test/03-09-2015-Bad-Results.csv"
            input_c = 0
            with open(data_path, mode='r', newline='') as csv_file:
                rd = csv.reader(csv_file, delimiter=',')
                for row in rd:

                    if input_c < site_count:
                        input_q.put(FilteredDomainData(domain=row[0]))
                        time.sleep(0.0001)
                    else:
                        break
                    input_c += 1

        input_t = threading.Thread(target=input_thread)
        input_t.start()

        while count < site_count:
            result = output_q.get()
            if result is not None:
                count += 1
                print("count:", count, "result:", str(result))
        test_filter.join(0)
        if input_t.is_alive():
            input_t.join()
        print("operation finished.")


class FilterTest(TestCase):

    @timeit()
    def testMozFilter1(self):
        input_q = queue.Queue()
        output_q = queue.Queue()

        stop_event = Event()
        input_param ={"input_queue": input_q, "output_queue": output_q, "stop_event": stop_event, "manager": AccountManager()}
        moz_filter = get_moz_filter(**input_param)
        moz_filter.start()
        site_count = 5000
        count = 0

        def input_thread():
            for i in range(site_count):
                input_q.put(FilteredDomainData(domain="domain{0:d}.com".format(i,)))
                time.sleep(0.0001)

        input_t = threading.Thread(target=input_thread)
        input_t.start()

        while count < site_count:
            result = output_q.get()
            if result is not None:
                count += 1
                print("count:", count, "result:", str(result))
        moz_filter.join(0)
        if input_t.is_alive():
            input_t.join()
        # for item in moz_filter._account_list:
        #     print(item)

    def testMozFilter2(self):
        moz_accounts = [moz_account, ]
        testThroughPut(MozFilter, accounts=moz_accounts, test_sites_count=25)

    def testArchiveProfileFilter1(self):
        input_param ={"input_queue": queue.Queue(), "output_queue": queue.Queue(), "stop_event": Event(),
                      "throughput_debug": True, "worker_number": 2}
        archive_filter = get_archive_filter(**input_param)
        links = FileIO.FileHandler.read_lines_from_file("/Users/superCat/Desktop/PycharmProjectPortable/test/archive_domain_test.txt")
        for link in links:
            site = FilteredDomainData(domain=link)
            archive_filter.process_data(data=site, )

    def testArchiveFilter2(self):
        testThroughPut(ArchiveOrgFilter, worker_number=30, test_sites_count=5000)

    def testMajesticFilter(self):

        filter = get_majestic_filter(worker_number=1, input_queue=Queue(), output_queue=Queue(), stop_event=Event())
        param = {"Account": majestic_account}
        links = FileIO.FileHandler.read_lines_from_file("/Users/superCat/Desktop/PycharmProjectPortable/test/spam_test2.txt")

        for link in links:
            link = LinkChecker.get_root_domain(link)[1]
            print("doing link:", link)
            site = FilteredDomainData(domain=link)
            filter.process_data(data=site, **param)

    def testSpamFilter(self):
        test_file_path = ""
        log_file_path = ""


    def testMajesticFilter2(self):

        filter = get_majestic_filter(worker_number=1, input_queue=Queue(), output_queue=Queue(), stop_event=Event(),
                                     en_tf_check=False, en_spam_check=True)
        param = {"Account": majestic_account}
        links = FileIO.FileHandler.read_lines_from_file("/Users/superCat/Desktop/PycharmProjectPortable/test/spam_test2.txt")

        for link in links:
            # link = LinkChecker.get_root_domain(link)[1]
            print("doing link:", link)
            site = FilteredDomainData(domain=link, tf=15, cf=15, ref_domains=10)
            filter.process_data(data=site, **param)

    def testArchiveFilter0(self):
        testThroughPut(MajesticFilter, worker_number=1, test_sites_count=100)

    def testFilterAll1(self):
        db_path = "/Users/superCat/Desktop/PycharmProjectPortable/sync/"
        manager = AccountManager(db_path)
        input_param ={"input_queue": queue.Queue(), "output_queue": queue.Queue(), "stop_event": Event(),
                      "throughput_debug": True, "worker_number": 2}
        file_path = "/Users/superCat/Desktop/PycharmProjectPortable/sync/Moz_filtering.csv"
        archive_filter = get_archive_filter(**input_param)
        majestic_filter = get_majestic_filter(**input_param)
        param = {"Account": majestic_account}
        count = 0
        with open(file_path, 'rt') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                link, da = row
                site = FilteredDomainData(domain=link, da=int(da))
                print(count, " process:", link)
                archive_data = archive_filter.process_data(data=site, )
                if archive_data is not None:
                    majestic_data = majestic_filter.process_data(data=site, **param)
                    print(majestic_data)
                count += 1

    def testRamdom(self):
        print(1 != 2)

    def testReadFromDb(self):
        db_path = "/Users/superCat/Desktop/PycharmProjectPortable/test/sync/FilteredSitesList"
        good_db = "/Users/superCat/Desktop/PycharmProjectPortable/test/sync/FilteredSitesList_Good"
        bad_db = "/Users/superCat/Desktop/PycharmProjectPortable/test/sync/FilteredSitesList_Bad"
        table = "01/10/2015 Gambling"
        db = FilteredResultDB(table=table, offset=0, db_addr=db_path)
        total_record = 10000
        patch = 10
        count = 0
        while count < total_record:
            sites = db.get_next_patch(patch, rollover=False)
            for item in sites:
                print("item number:", count, " ", item)
                count += 1

    def testWriteToDb(self):
        db_path = "/Users/superCat/Desktop/PycharmProjectPortable/sync/FilteredSitesList"
        good_db = "/Users/superCat/Desktop/PycharmProjectPortable/sync/Majestic_filtering_good.csv"
        table = "20/12/2015 Legal"
        db = FilteredResultDB(table=table, offset=0, db_addr=db_path)
        count = 0
        temp_sites = []
        with open(good_db, mode='r', newline='') as csv_file:
            rd = csv.reader(csv_file, delimiter=',')
            for row in rd:
                if int(row[10]) > 1450612100:
                    data = FilteredDomainData.from_tuple(row)
                    print(data.__dict__)
                    count += 1
                    temp_sites.append(data)
        print("total:", count)
        db.add_sites(temp_sites, skip_check=False)
        db.close()

    def testFilterPool(self):
        self._stop_event = Event()
        filter_matrix = CrawlMatrix(tf=15, cf=15, da=15, ref_domains=10, tf_cf_deviation=0.8)
        # filter_matrix = FilteredDomainData(tf=15, cf=15, da=15, ref_domains=10, tf_cf_deviation=0.80)
        self._db_ref = "something"
        self._input_queue = Queue()
        self._output_queue = Queue()
        self._pool_input = Queue()
        self._queue_lock = RLock()
        pool = FilterPool(self._pool_input, self._output_queue, self._queue_lock, self._stop_event, matrix=filter_matrix,
                                )
        pool.start()
        while True:
            time.sleep(1)
