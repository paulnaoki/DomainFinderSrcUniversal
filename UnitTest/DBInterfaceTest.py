from unittest import TestCase
from DomainFinderSrc.Scrapers.SiteTempDataSrc.ExternalTempDataDiskBuffer import ExternalTempDataDiskBuffer
from threading import Event
from DomainFinderSrc.MiniServer.Common.DBInterface import ExternalSiteDB


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