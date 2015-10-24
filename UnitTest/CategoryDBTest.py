from unittest import TestCase
from DomainFinderSrc.MiniServer.DatabaseServer.SiteDB import *

site_db_addr = "/Users/superCat/Desktop/PycharmProjectPortable/test/db/CategoryDomainSiteDBTest.db"


class SiteDBTest(TestCase):
    def testAdd(self):
        site_db = CategoryDomainSiteDB(site_db_addr)
        sites = []
        sites.append(CatagoryDomainSiteDataStruct("godaddy.com",))
        sites.append(CatagoryDomainSiteDataStruct("somethingwrong.com",))
        site_db.add_sites(sites, skip_check=False)
        results = site_db.get_next_patch_no_rollover(0, 1000)
        for item in results:
            print(item)



