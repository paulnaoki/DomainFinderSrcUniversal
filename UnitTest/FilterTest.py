from unittest import TestCase
from DomainFinderSrc.Scrapers.MatrixFilter import *
from DomainFinderSrc.Scrapers.MatrixFilterControl import *
from multiprocessing import Event
import queue
import csv
from UnitTest.Accounts import account
from DomainFinderSrc.MiniServer.Common.DBInterface import FilteredResultDB


def get_archive_filter() -> ArchiveOrgFilter:
    input_param ={"input_queue": queue.Queue(), "output_queue": queue.Queue(), "stop_event": Event()}
    archive_filter = ArchiveOrgFilter(**input_param)
    return archive_filter


def get_majestic_filter() -> MajesticFilter:
        manager = AccountManager()
        manager.AccountList.append(account)
        input_param ={"input_queue": queue.Queue(), "output_queue": queue.Queue(), "stop_event": Event()}
        filter = MajesticFilter(manager=manager, **input_param)
        return filter


class FilterTest(TestCase):
    def testArchiveProfileFilter1(self):
        archive_filter = get_archive_filter()
        links = FileIO.FileHandler.read_lines_from_file("/Users/superCat/Desktop/PycharmProjectPortable/test/archive_domain_test.txt")
        for link in links:
            site = FilteredDomainData(domain=link)
            archive_filter.process_data(data=site, )

    def testMajesticFilter(self):
        filter = get_majestic_filter()
        param = {"Account": account}
        links = FileIO.FileHandler.read_lines_from_file("/Users/superCat/Desktop/PycharmProjectPortable/test/spam_test1.txt")

        for link in links:
            site = FilteredDomainData(domain=link)
            filter.process_data(data=site, **param)

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
