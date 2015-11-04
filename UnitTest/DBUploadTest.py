from unittest import TestCase
from DomainFinderSrc.MajesticCom import *
from DomainFinderSrc.SiteConst import *
from DomainFinderSrc.Scrapers.MatrixFilter import MajesticFilter
from DomainFinderSrc.Scrapers.SiteTempDataSrc.DataStruct import FilteredDomainData
from DomainFinderSrc.Utilities import FileIO, Logging
from DomainFinderSrc.ComboSites.GoogleMajetic import GoogleMajestic, GoogleCom
from DomainFinderSrc.MajesticCom.Category import *
from UnitTest.Accounts import majestic, account
from DomainFinderSrc.MiniServer.DatabaseServer.CategoryDB import CategoryDBManager
from DomainFinderSrc.MiniServer.DatabaseServer.CategorySiteDB import CategorySeedSiteDB, CategorySiteDBManager
from DomainFinderSrc.Utilities.Serializable import Serializable
from DomainFinderSrc.MiniServer.Common.DBInterface import *
import random


def get_seeds(categoy_db_addr: str,  seed_limit: int, niche: str, parameters: dict):
        db = CategorySeedSiteDB(categoy_db_addr)
        if niche.endswith("General"):
            niche = niche.rstrip("General")

        temp_sites = []
        target_ca = []
        sites = []
        categories = db.get_sub_category_tables_name()
        target_ca += [x for x in categories if niche in x]

        load_limit = seed_limit * 4
        for ca in target_ca:
            print("getting seeds from:", ca)
            temp_sites += [x.ref_domain for x in db.get_from_table(ca, 0, load_limit, parameters)]

        seed_count = len(temp_sites)

        if seed_count <= seed_limit:
            sites = temp_sites
        elif seed_limit < seed_count <= seed_limit * 2:
            sites = temp_sites[::2]
        else:
            while len(sites) < seed_limit:
                site = temp_sites[random.randint(0, seed_count-1)]
                if site not in sites:
                    sites.append(site)
        return sites


class SeedUploadTest(TestCase):
    def testUpload1(self):
        seed_db_addr = "/Users/superCat/Desktop/PycharmProjectPortable/sync/SeedSitesList"
        seed_db = SeedSiteDB("03/11/2015 CF5", db_addr=seed_db_addr)

        categoy_db_addr = "/Users/superCat/Desktop/PycharmProjectPortable/Seeds/CategorySeedDB.db"
        db = CategorySeedSiteDB(categoy_db_addr)

        target_ca = ["Health/General", "Shopping/General", "Business/Information Technology",
                     "Business/Construction and Maintenance", "Health/Nutrition"]
        seeds_needed = 5000
        parameters = {"CF": 5}
        for ca in target_ca:
            sites = get_seeds(categoy_db_addr, seeds_needed, ca, parameters)
            print("doing site:", ca, " size:", len(sites))
            seed_db.add_sites(sites, skip_check=False)
        seed_db.close()
