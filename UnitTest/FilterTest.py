from unittest import TestCase
from DomainFinderSrc.Scrapers.MatrixFilter import *
from DomainFinderSrc.Scrapers.MatrixFilterControl import *
from multiprocessing import Event
import queue
import csv
from UnitTest.Accounts import account
from DomainFinderSrc.MiniServer.Common.DBInterface import FilteredResultDB
from DomainFinderSrc.Scrapers.SiteTempDataSrc.DataStruct import FilteredDomainData
from DomainFinderSrc.Utilities.TimeIt import timeit
import threading
import csv


def get_archive_filter(**input_param) -> ArchiveOrgFilter:
    archive_filter = ArchiveOrgFilter(**input_param)
    return archive_filter


def get_majestic_filter() -> MajesticFilter:
        manager = AccountManager()
        manager.AccountList.append(account)
        input_param ={"input_queue": queue.Queue(), "output_queue": queue.Queue(), "stop_event": Event()}
        majestic_filter = MajesticFilter(manager=manager, **input_param)
        return majestic_filter


def get_moz_filter(input_q, output_q, stop_event, throughput_debug=False) -> MozFilter:
    db_path = "/Users/superCat/Desktop/PycharmProjectPortable/sync/"
    manager = AccountManager(db_path)
    input_param ={"input_queue": input_q, "output_queue": output_q, "stop_event": stop_event}
    moz_filter = MozFilter(manager=manager, throughput_debug=throughput_debug, **input_param)
    return moz_filter


def testThroughPut(fil, worker_number: int, test_sites_count=5000):
        manager = AccountManager()
        input_q = queue.Queue()
        output_q = queue.Queue()

        stop_event = Event()
        input_param ={"input_queue": input_q, "output_queue": output_q, "stop_event": stop_event,
                      "throughput_debug": True,
                      "worker_number": worker_number,
                      "manager": manager}

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
        input_param ={"input_queue": input_q, "output_queue": output_q, "stop_event": stop_event}
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
        filter = get_majestic_filter()
        param = {"Account": account}
        links = FileIO.FileHandler.read_lines_from_file("/Users/superCat/Desktop/PycharmProjectPortable/test/spam_test1.txt")

        for link in links:
            site = FilteredDomainData(domain=link)
            filter.process_data(data=site, **param)

    def testArchiveFilter0(self):
        testThroughPut(MajesticFilter, worker_number=1, test_sites_count=100)

    def testFilterAll1(self):
        file_path = "/Users/superCat/Desktop/PycharmProjectPortable/sync/Moz_filtering.csv"
        archive_filter = get_archive_filter()
        majestic_filter = get_majestic_filter()
        param = {"Account": account}
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
