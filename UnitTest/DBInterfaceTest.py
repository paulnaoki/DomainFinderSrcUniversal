from unittest import TestCase
from DomainFinderSrc.Scrapers.SiteTempDataSrc.ExternalTempDataDiskBuffer import ExternalTempDataDiskBuffer
from threading import Event
from DomainFinderSrc.MiniServer.Common.DBInterface import ExternalSiteDB, FilteredResultDB
from DomainFinderSrc.Utilities.Logging import CsvLogger


class testDB(TestCase):
    def testExternalDbBuffer(self):
        backup_db_addr = "/Users/superCat/Desktop/PycharmProjectPortable/sync/ResultSitesList.db"
        table = "24/10/2015 Gardening"
        backup_db = ExternalSiteDB(table, db_addr=backup_db_addr)
        total = backup_db.site_count(False)
        count = 0
        db_addr = "/Users/superCat/Desktop/PycharmProjectPortable/sync/"
        stop_event = Event()
        db_buffer = ExternalTempDataDiskBuffer("TempDB.db", None, stop_event, dir_path=db_addr)
        db_buffer._input_convert_tuple = False
        while count < total:
            results = backup_db.get_next_patch_no_rollover(count, 5000)
            print(count)
            db_buffer.write(results)
            count += 5000

    def testFilterExportDB(self):
        from_addr = "/Users/superCat/Desktop/PycharmProjectPortable/sync/FilteredSitesList_oLD"
        to_addr = "/Users/superCat/Desktop/PycharmProjectPortable/sync/FilteredSitesList"
        table_name = "20/11/2015"
        from_db = FilteredResultDB(table_name, db_addr=from_addr)
        to_db = FilteredResultDB(table_name, db_addr=to_addr)
        results = [x for x in from_db.get_all_sites() if x[1] > 0]
        count = 0
        for item in results:
            print("count:", count, "item:", item)
            count += 1
        # to_db.add_sites(results, skip_check=True)

    def testFilterExportDB2(self):
        from_addr = "/Users/superCat/Desktop/PycharmProjectPortable/sync/FilteredSitesList.db"
        to_addr = "/Users/superCat/Desktop/PycharmProjectPortable/sync/Sum.db"
        table_name = "20/11/2015"
        from_db = FilteredResultDB(table_name, db_addr=from_addr)
        from_db.cur.execute("SELECT name FROM sqlite_master WHERE type = 'table';")
        table_names = [x[0] for x in from_db.cur.fetchall()]
        to_db = FilteredResultDB("2015 Old", db_addr=to_addr)
        for table_name in table_names:
            print(table_name)
            temp = FilteredResultDB(table_name, db_addr=from_addr)
            results = [x for x in temp.get_all_sites() if x[1] > 0]
            temp.close()
            count = 0
            for item in results:
                print("count:", count, "item:", item)
                count += 1
            to_db.add_sites(results, skip_check=True)
        from_db.close()
        to_db.close()

    def testExportCsv(self):
        from_addr = "/Users/superCat/Desktop/PycharmProjectPortable/sync/Sum.db"
        to_addr = "/Users/superCat/Desktop/PycharmProjectPortable/sync/2015_OLD.csv"
        table_name = "2015 Old"
        from_db = FilteredResultDB(table_name, db_addr=from_addr)
        data = [x for x in from_db.get_all_sites() if x[1] > 0]
        CsvLogger.log_to_file_path(to_addr, [FilteredResultDB.get_fields_names(),])
        CsvLogger.log_to_file_path(to_addr, data)