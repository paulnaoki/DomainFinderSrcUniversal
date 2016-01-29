from DomainFinderSrc.AmazonServiceCom import Const
from DomainFinderSrc.MiniServer.DomainMiningSlaveServer.MiningSlaveController import MiningController
from unittest import TestCase
from DomainFinderSrc.MiniServer.DatabaseServer.CategorySiteDB import CategorySeedSiteDB, CategorySiteDBManager
from DomainFinderSrc.MiniServer.Common.DBInterface import *
import random
from DomainFinderSrc.MiniServer.DomainMiningMasterServer.HostController import *
from DomainFinderSrc.UserAccountSettings.UserAccountDB import DBFilterCollection, SeedSiteFilter, FilteredResultFilter, ExternalSiteDBFilter
from UnitTest.Accounts import moz_account, majestic_account
import csv
from DomainFinderSrc.MozCom import *
from DomainFinderSrc.SiteConst import *


def get_server():
    return Server(address=ServerAddress("54.191.238.226", 9999))
    #return Server(address=ServerAddress("52.88.37.117", 9999))

seed_db_name = "29/01/2016 Generic"
launch_group = "jan291"


def setup(ser: Server, data: SetupData):

    try:
        if isinstance(data, SetupData):  # forwards to the central control
            ser = ser
            hostController = HostController(ser, cmd=ServerCommand.Com_Setup, in_data=data)
            hostController.start()
            hostController.join()
            print("setup successfully.")
        else:
            ErrorLogger.log_error("something is wrong in the setup:", Exception("get back wrong data type, should be SetupData"), str(type(data)))
    except Exception as ex:
        print("something is wrong in the setup:", ex)
        ErrorLogger.log_error("something is wrong in the setup:", ex, str(data))


def get_seeds(categoy_db_addr: str,  seed_limit: int, niche: str, parameters: dict):
        db = CategorySeedSiteDB(categoy_db_addr)
        # if niche.endswith("General"):
        #     niche = niche.rstrip("General")

        temp_sites = []
        target_ca = []
        sites = []
        categories = db.get_sub_category_tables_name()
        target_ca += [x for x in categories if niche in x]

        load_limit = seed_limit * 5
        for ca in target_ca:
            print("getting seeds from:", ca)
            temp_sites += [x.ref_domain for x in db.get_from_table(ca, 0, load_limit, random_read=True,
                                                                   filter_dict=parameters)]

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


def get_seeds_normal(categoy_db_addr: str,  seed_limit: int, niche: str, parameters: dict):
    db = CategorySeedSiteDB(categoy_db_addr)
    temp = [x.ref_domain for x in db.get_from_table(niche, 0, seed_limit, random_read=False,
                                                                   filter_dict=parameters)]
    db.close()
    return temp


def clear_slave_cache(slave_server_addrs: list):
    slave_servers = [Server(server_type=ServerType.ty_MiningSlaveSmall, address=ServerAddress(x, 9999)) for x in slave_server_addrs]
    threads = []
    for slave in slave_servers:
        if isinstance(slave, Server):
            threads.append(MiningController(slave, cmd=ServerCommand.Com_Clear_Cache))
    if len(threads) > 0:
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        threads.clear()


class SeedUploadTest(TestCase):
    def test_s(self):
        accounts = self.test_get_moz_accounts(10)
        accounts.append(majestic_account)
        data = SetupData("something", cap2=165, cap3=3, max_page_level=999, max_page_limit=1000, accounts=accounts)
        print(data.get_serializable_json())

    def testUpload1(self):
        sock = StreamSocket()
        processor = CommandProcessor(sock.rfile, sock.wfile)

        seed_db_addr = "/Users/superCat/Desktop/PycharmProjectPortable/sync/SeedSitesList"
        seed_db = SeedSiteDB("09/11/2015", db_addr=seed_db_addr)

        categoy_db_addr = "/Users/superCat/Desktop/PycharmProjectPortable/Seeds/CategorySeedDB.db"
        db = CategorySeedSiteDB(categoy_db_addr)

        target_ca = ["Health/General", "Health/Nutrition", "Shopping/Clothing", "Computers/Internet/Web Design and Development",
                     "Society/People", "Home/Gardening", "Computers/Hardware", "Recreation/Food"]
        seeds_needed = 5000
        parameters = {"CF": 0}
        for ca in target_ca:
            sites = get_seeds(categoy_db_addr, seeds_needed, ca, parameters)
            print("doing site:", ca, " size:", len(sites))
            seed_db.add_sites(sites, skip_check=False)
        seed_db.close()

    def testSeedUpload3(self):
        db_addr = "/Users/superCat/Desktop/PycharmProjectPortable/Seeds/BlogSeedDB.db"
        db = SeedSiteDB(table="Society/Law", db_addr=db_addr)
        sites = [x[0] for x in db.get_all_sites()]
        for item in sites:
            print(item)
        # in_data = MiningList(ref=seed_db_name, data=sites)
        # ser = get_server()
        # hostController = HostController(ser, cmd=ServerCommand.Com_Add_Seed, in_data=in_data)
        # hostController.start()
        # hostController.join()

    def testSeedsUpload2(self) -> int:
        categoy_db_addr = "/Users/superCat/Desktop/PycharmProjectPortable/Seeds/NewCategorySeedDB.db"
        # categoy_db_addr = "/Users/superCat/Desktop/PycharmProjectPortable/Seeds/CategorySeedDB2.db"
        target_ca = {
        "Games/Gambling": 62000,
        # "Society/Politics":20000,
        # "Society/Issues":20000,
        # "Business/Financial Services":20000,
        }

        # seeds_needed = 20000
        total_seeds = 0
        parameters = {"TF": 0}
        db = CategorySeedSiteDB(categoy_db_addr)
        for ca, seeds_needed in target_ca.items():
            sites = [x.ref_domain for x in db.get_from_table(ca, 68000, seeds_needed, random_read=False, reverse_read=False,
                                                                           filter_dict=parameters)]
            # sites = get_seeds_normal(categoy_db_addr, seeds_needed, ca, parameters)
            total_seeds += len(sites)
            print("doing site:", ca, " size:", len(sites))
            in_data = MiningList(ref=seed_db_name, data=sites)
            ser = get_server()
            hostController = HostController(ser, cmd=ServerCommand.Com_Add_Seed, in_data=in_data)
            hostController.start()
            hostController.join()
        db.close()
        if len(target_ca) > 1:
            return total_seeds * 0.97
        else:
            return total_seeds

    def testSeedsUpload_General(self) -> int:
        categoy_db_addr = "/Users/superCat/Desktop/PycharmProjectPortable/Seeds/CategorySeedDB3.db"
        # categoy_db_addr = "/Users/superCat/Desktop/PycharmProjectPortable/Seeds/CategorySeedDB2.db"
        db = CategorySeedSiteDB(categoy_db_addr)
        categories = db.get_sub_category_tables_name()
        forbidden_niche = ['Adult/', 'Gambling', 'Law', 'Directory']
        target_ca = {
        }
        seed_count = 200
        for item in categories:
            if not any(x in item for x in forbidden_niche):
                target_ca.update({item:seed_count})
        # seeds_needed = 20000
        total_seeds = 0
        in_data = MiningList(ref=seed_db_name, data=[])
        parameters = {"TF": 5}
        counter = 0
        for ca, seeds_needed in target_ca.items():
            sites = get_seeds_normal(categoy_db_addr, seeds_needed, ca, parameters)
            total_seeds += len(sites)
            print(counter, " doing site:", ca, " size:", len(sites), " total:", total_seeds)
            in_data.data += sites
            counter += 1
        ser = get_server()
        hostController = HostController(ser, cmd=ServerCommand.Com_Add_Seed, in_data=in_data)
        hostController.start()
        hostController.join()
        if len(target_ca) > 1:
            return total_seeds * 0.97
        else:
            return total_seeds

    def test_get_moz_accounts(self, count: int=25) -> []:
        account_list = []
        temp = 0
        offset = 60
        if count > 0:
            file_path = "/Users/superCat/Desktop/PycharmProjectPortable/test/accounts/good_accounts_backup.csv"
            with open(file_path, mode='r', newline='') as csv_file:
                reader = csv.reader(csv_file, delimiter=',')
                for email, psd, user_name, access_id, api_key in reader:
                    try:
                        if temp > offset:
                            print("count", temp, "email:", email, "psd:", psd, " user_name:", user_name, " access_id:", access_id,)
                            account = SiteAccount(siteType=AccountType.Moz, userID=email, password=psd, AccessID=access_id, APIkey=api_key)
                            account_list.append(account)
                        temp += 1
                    except Exception as ex:
                        print(ex)
                    finally:
                        if temp >= count+offset:
                            break
        return account_list

    def testClearCache(self):
        from UnitTest.EC2Test import EC2Test
        get_ec2_instances_tester = EC2Test()
        tag_value = launch_group
        public_ips = get_ec2_instances_tester.testGetInstanceByTag(tag_value)[1]
        clear_slave_cache(public_ips)

    def test_get_status(self):
        slave = Server(address=ServerAddress("54.200.205.152", 9999))
        t = MiningController(slave, cmd=ServerCommand.Com_Status)
        t.start()
        t.join(10)
        print(slave.status)

    def testStartCrawl(self):

        from UnitTest.EC2Test import EC2Test
        get_ec2_instances_tester = EC2Test()
        tag_value = launch_group
        moz_account_count = 30
        instance_count = 20
        warm_up_time_min = 5
        # total_seeds = self.testSeedsUpload2()
        # total_seeds = None
        total_seeds = 88856
        offset = 0
        print("total seed:", total_seeds)
        accounts = self.test_get_moz_accounts(moz_account_count)
        accounts.append(majestic_account)
        private_ips = get_ec2_instances_tester.testAutomationFlow1(instance_count, tag_value, zone=Const.Zone.US_West_2C)
        # private_ips = get_ec2_instances_tester.testGetInstanceByTag(tag_value)[0]
        seed_filter = SeedSiteFilter(update_interval=2400)
        temp_result_filter = ExternalSiteDBFilter(update_interval=30)
        result_filter = FilteredResultFilter(update_interval=30)
        setup_data = SetupData(ref=seed_db_name, cap=1, cap2=230, cap3=2, total=total_seeds,
                               offset=offset,
                               max_page_level=999, max_page_limit=20000, loopback=False,
                               db_filter=DBFilterCollection(seed=seed_filter, external=temp_result_filter, filteredResult=result_filter, save=True),
                               crawl_matrix=CrawlMatrix(da=10, tf=15, cf=15, ref_domains=10, tf_cf_deviation=0.8,
                                                        en_moz=True, en_archive_check=True, en_archive_count=True,
                                                        en_majestic=True, en_spam_check=True),
                               accounts=accounts,
                               addtional_data=SlaveOperationData(ref=seed_db_name, count=len(private_ips), slaves_addrs=private_ips))
        print("warm up time...")
        time.sleep(warm_up_time_min*60)
        print("warm up finished...")
        setup(get_server(), setup_data)

    def test_terminate(self):
        from UnitTest.EC2Test import EC2Test
        get_ec2_instances_tester = EC2Test()
        get_ec2_instances_tester.testTerminateWithTimeout(timeout=0, tag_v=launch_group)

    def test_min(self):
        items = [1.0,2.5,4.6]
        print(min(items))

    def testStartCrawlLocal(self):
        private_ips = ["54.200.205.152", ]
        db_name = "GamblingSeeds2"
        ser = Server(address=ServerAddress("127.0.0.1", 9998))
        #accounts = [majestic_account, moz_account]
        accounts = self.test_get_moz_accounts(1)
        accounts.append(majestic_account)
        total_seeds = 12600
        seed_filter = SeedSiteFilter(update_interval=1200)
        temp_result_filter = ExternalSiteDBFilter(update_interval=30)
        result_filter = FilteredResultFilter(update_interval=30)
        setup_data = SetupData(ref=db_name, cap=len(private_ips), cap2=200, cap3=2, total=total_seeds, offset=300,
                               max_page_level=999, max_page_limit=3000, loopback=False,
                               db_filter=DBFilterCollection(seed=seed_filter, external=temp_result_filter, filteredResult=result_filter, save=True),
                               crawl_matrix=CrawlMatrix(da=15, tf=15, cf=15, ref_domains=10, tf_cf_deviation=0.8),
                               accounts=accounts,
                               addtional_data=SlaveOperationData(ref=db_name, count=len(private_ips), slaves_addrs=private_ips))
        setup_s = setup_data.get_serializable_json()
        print(setup_s)
        result = Serializable.get_deserialized_json(setup_s)
        print(result)
        setup(ser, setup_data)

    def testStartFiltering(self):
        # db_name = "FashionShopping"
        db_name = seed_db_name
        # local_ser = Server(address=ServerAddress("127.0.0.1", 9998))
        local_ser = get_server()
        #accounts = [majestic_account, moz_account]
        accounts = self.test_get_moz_accounts(25)
        accounts.append(majestic_account)

        setup_data = FilteringSetupData(ref=db_name, offset=100000, total=255215,
                                        crawl_matrix=CrawlMatrix(da=15, tf=15, cf=15, ref_domains=10, tf_cf_deviation=0.8),
                                        accounts=accounts,)
        setup_s = setup_data.get_serializable_json()
        print(setup_s)
        result = Serializable.get_deserialized_json(setup_s)
        print(result)
        try:
            hostController = HostController(local_ser, cmd=ServerCommand.Com_Start_Filter, in_data=setup_data)
            hostController.start()
            hostController.join()
            print("setup successfully.")

        except Exception as ex:
            print("something is wrong in the setup:", ex)


