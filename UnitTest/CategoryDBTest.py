from unittest import TestCase
from DomainFinderSrc.MiniServer.Common.DBInterface import *
from DomainFinderSrc.MiniServer.DatabaseServer.SiteDB import *
from DomainFinderSrc.MiniServer.DomainMiningMasterServer.HostController import *
import math
from DomainFinderSrc.MiniServer.DatabaseServer.MarketplaceDBManager import MarketplaceDBManager
from DomainFinderSrc.MiniServer.DatabaseServer.CategorySiteDB import CategorySeedSiteDB

def get_server():
    return Server(address=ServerAddress("52.88.37.117", 9999))

site_test_db_addr = "/Users/superCat/Desktop/PycharmProjectPortable/Results/MarketplaceSkeletonSites.db"
site_real_db_addr = "/Users/superCat/Desktop/PycharmProjectPortable/Results/MarketplaceSites.db"


class SiteDBTest(TestCase):
    def testAdd(self):
        site_db = CategoryDomainSiteDB(site_test_db_addr)
        sites = []
        sites.append(CatagoryDomainSiteDataStruct("godaddy.com",))
        sites.append(CatagoryDomainSiteDataStruct("somethingwrong.com",))
        site_db.add_sites(sites, skip_check=False)
        results = site_db.get_next_patch_no_rollover(0, 1000)
        for item in results:
            print(item)

    def testComplexSelect(self):
        db = CategoryDomainSiteDB(site_real_db_addr)
        niches = "\'News/Newspapers\'"
        min_topical_s = 10
        results = db.cur.execute("SELECT * FROM CategoryDomain WHERE TF>=15 AND ((TOPIC1 IN ({0:s}) AND TOPIC1_S >= {1:d})"
                                 " OR (TOPIC2 IN ({0:s}) AND TOPIC2_S >= {1:d}) OR (TOPIC3 IN ({0:s}) AND TOPIC3_S >={1:d})) "
                                 "ORDER BY rowid LIMIT 100".format(niches, min_topical_s, ))
        for item in results:
            print(item)
        db.close()

    def testComlexQuery(self):
        db = CategoryDomainSiteDB(site_real_db_addr)
        parameters = {
            "TF": 10,
            "DA": 10,
            "CF": 10,
            "TOPIC1": "News/Newspapers",
            # "TOPIC2": "Business/Information Services",
            "TOPIC1_S": 15,
        }
        data = db.get_next_patch_no_rollover(0, 100, **parameters)
        db.close()
        for item in data:
            print(item)

    def testAddFromRemote(self):
        index = 0
        length = 3890
        max_len_per_query = 2000
        db_name = "20/11/2015"

        query_count = int(math.ceil(length / max_len_per_query))
        ser = get_server()
        FileHandler.create_file_if_not_exist(site_real_db_addr)
        site_db = CategoryDomainSiteDB(site_real_db_addr)
        total_result = []
        outputBuffer = []
        sites = []
        try:
            for i in range(0, query_count):
                db_request = DBRequestFields(db_name=db_name, db_type=DBType.Type_Filtered_Result, index=index, length=max_len_per_query)
                hostController = HostController(ser, cmd=ServerCommand.Com_Get_DB_DATA, in_data=db_request, out_data=outputBuffer)
                hostController.start()
                hostController.join()
                return_data = outputBuffer[0]
                if len(outputBuffer) > 0 and isinstance(return_data, MiningList):
                    total_result += return_data.data
                    index += len(return_data.data)
                    outputBuffer.clear()

        except Exception as ex:
            print(ex, " name:" + db_name)
        for item in total_result:
            temp = FilteredDomainData.from_tuple(item)
            if isinstance(temp, FilteredDomainData):
                converted = CatagoryDomainSiteDataStruct.from_FilteredDomainData(temp)
                sites.append(converted)
        site_db.add_sites(sites, skip_check=False)
        site_db.close()

    def testSeedUpdate(self):
        stop_event = threading.Event()
        manager = MarketplaceDBManager(stop_event=stop_event, db_addr=site_real_db_addr, skeleton_db_addr=site_test_db_addr)
        manager.update_db()
        stats = manager.get_db_stats()
        if isinstance(stats, MiningList):
            for item in stats.data:
                print(item)

    def test_merge_db(self):
        merge_from = "/Users/superCat/Desktop/PycharmProjectPortable/Seeds/CategorySeedDB2.db"
        merge_to = "/Users/superCat/Desktop/PycharmProjectPortable/Seeds/CategorySeedDB.db"
        db_from = CategorySeedSiteDB(merge_from)
        db_to = CategorySeedSiteDB(merge_to)
        from_cat = db_from.get_sub_category_tables_name()
        for item in from_cat:
            results = db_from.get_from_table(item, 0, 10000000, reverse_read=False, random_read=False)
            print("adding:", item, "result:", len(results))
            db_to.save_to_table(item, results)

