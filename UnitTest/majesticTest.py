from multiprocessing import Event
import queue
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


def parse_majestic_topic(topics: str) -> [SubCategory]:
    splited_topics = topics.split(";")
    catagories = []
    for item in splited_topics:
        if len(item) == 0:
            continue
        topic, trust_flow = item.split(":")
        if len(topic) == 0 or len(trust_flow) == 0:
            continue
        else:
            parsed_catagory = CategoryManager.decode_sub_category(topic)
            catagories.append(parsed_catagory)
            print(parsed_catagory)
    return catagories


def is_valid_ISO8859_1_str(original_str: str) -> bool:
    try:
        temp = original_str.encode(encoding='iso-8859-1').decode(encoding='iso-8859-1')
        if temp == original_str:
            return True
        else:
            return False
    except:
        return False


def convert_to_regular_expression(keyword: str):
    if is_valid_ISO8859_1_str(keyword):
        pass


def backlink_callback(backlink: MajesticBacklinkDataStruct):
    logging_path = "/Users/superCat/Desktop/PycharmProjectPortable/Seeds/Gambling3.csv"
    print(backlink)
    Logging.CsvLogger.log_to_file_path(logging_path, [backlink.to_tuple(), ])


class MajesticTest(TestCase):

    def testTF_CF(self):
        data = majestic.get_cf_tf_list(["www.articleroller.com", "http://www.articleroller.com"], True)
        for item in data:
            print(item)

    def test_anchor_text(self):
        data = majestic.get_anchor_text_info(domain="susodigital.com", is_dev=False)
        print(data)
        print("number of data points: ", len(data[0]))

    def test_ref_domains(self):
        data = majestic.get_ref_domains(domain="susodigital.com", is_dev=False)
        for item in data:
            print(item)

    def testWesternLan(self):
        strs = ["travel log", "something", "中国字", "Агент Mail.Ru", "conférence des communautés homosexuelle"]
        for original_str in strs:
            print(original_str, " is valid?:", is_valid_ISO8859_1_str(original_str))

    def test_filter_ref_domain(self):
        def _filter_ref_domains(domain: str) -> bool:
            max_bad_country_ratio = 0.1
            bad_country_count = 0
            max_backlinks_for_single_bad_country = 30
            _bad_country = ["CN", "JP", "KO", "RU"]
            ref_domains = []
            ref_domains.append(MajesticRefDomainStruct("bbc.co.uk", tf=99, cf=78, country="UK", backlinks=5000, ref_domains=3000))
            ref_domains.append(MajesticRefDomainStruct("cnn.org", tf=70, cf=67, country="US", backlinks=4000, ref_domains=3000))
            ref_domains.append(MajesticRefDomainStruct("csa.co.uk", tf=99, cf=78, country="UK", backlinks=5000, ref_domains=3000))
            ref_domains.append(MajesticRefDomainStruct("sina.org", tf=70, cf=67, country="CN", backlinks=25, ref_domains=3000))
            ref_domains.append(MajesticRefDomainStruct("bbc.co.jp", tf=99, cf=78, country="JP", backlinks=10, ref_domains=3000))
            ref_domains.append(MajesticRefDomainStruct("ahref.com", tf=70, cf=67, country="CN", backlinks=20, ref_domains=3000))
            ref_domains.append(MajesticRefDomainStruct("bbc.co.uk", tf=99, cf=78, country="UK", backlinks=5000, ref_domains=3000))
            ref_domains.append(MajesticRefDomainStruct("cnn.org", tf=70, cf=67, country="US", backlinks=4000, ref_domains=3000))
            ref_domains.append(MajesticRefDomainStruct("bbc.co.uk", tf=99, cf=78, country="UK", backlinks=5000, ref_domains=3000))
            ref_domains.append(MajesticRefDomainStruct("cnn.org", tf=70, cf=67, country="US", backlinks=4000, ref_domains=3000))
            ref_domains.append(MajesticRefDomainStruct("bbc.co.uk", tf=99, cf=78, country="UK", backlinks=5000, ref_domains=3000))
            ref_domains.append(MajesticRefDomainStruct("cnn.org", tf=70, cf=67, country="US", backlinks=4000, ref_domains=3000))
            ref_domains.append(MajesticRefDomainStruct("bbc.co.uk", tf=99, cf=78, country="UK", backlinks=5000, ref_domains=3000))
            ref_domains.append(MajesticRefDomainStruct("cnn.org", tf=70, cf=67, country="US", backlinks=4000, ref_domains=3000))
            total_record = len(ref_domains)
            for ref_domain in ref_domains:
                if isinstance(ref_domain, MajesticRefDomainStruct):
                    if ref_domain.country in _bad_country:
                        bad_country_count += 1
                        if ref_domain.backlinks > max_backlinks_for_single_bad_country:
                            raise ValueError("{0:s} from bad country has more than {1:d} backlinks.".format(ref_domain.domain,max_backlinks_for_single_bad_country))

            bad_country_ratio = bad_country_count/total_record
            if total_record > 0 and bad_country_ratio > max_bad_country_ratio:
                raise ValueError("bad country ratio in ref domains is too high: {0:.1f} percent.".format(bad_country_ratio*100,))
            return True
        print(_filter_ref_domains("bbc.com"))

    def testAnchorText(self):
        self._spam_anchor = ["tit", "sex", "oral sex", "熟女"]

        def isOK(domain: str):
            min_anchor_variation_limit = 2
            no_follow_limit = 0.5
            domain_contain_limit = 5
            is_in_anchor = False
            temp_list = ["boot", "tistd", "bbc.co.uk", "ok", "美熟女", "中国", "afafa", "fafa"]
            #temp_list = ["boot", "tistd", "ok", "中国", "熟女s", "bbc.co.uk"]
            anchor_list, total, deleted, nofollow = (temp_list, 1000, 200, 100)  # change this
            if len(anchor_list) <= min_anchor_variation_limit:
                raise ValueError("number of anchor variation is less than 2.")
            elif (deleted + nofollow)/total > no_follow_limit:
                raise ValueError("deleted and nofollow backlinks are more than 50%.")
            elif len(self._spam_anchor) > 0:
                count = 0
                for anchor in anchor_list:
                    if domain in anchor and count < domain_contain_limit:
                        is_in_anchor = True

                    # if not MajesticFilter._is_valid_ISO8859_1_str(anchor):
                    #     raise ValueError("anchor contains invalid western language word: {0:s}.".format(anchor,))
                    for spam in self._spam_anchor:
                        # pattern = re.compile(spam, re.IGNORECASE)
                        # if re.search(pattern, anchor):
                        if spam in anchor:
                            raise ValueError("anchor {0:s} is in spam word {1:s}".format(anchor, spam))
                    count += 1

            if not is_in_anchor:
                raise ValueError("anchor does not have the domain name in top {0:d} results.".format(domain_contain_limit,))

            return True

        domain = "bbc.co.uk"
        print(isOK(domain))

    def testFilter(self):
        manager = AccountManager()
        manager.AccountList.append(account)
        input_param ={"input_queue": queue.Queue(), "output_queue": queue.Queue(), "stop_event": Event()}
        filter = MajesticFilter(manager=manager, **input_param)
        param = {"Account": account}
        links = FileIO.FileHandler.read_lines_from_file("/Users/superCat/Desktop/PycharmProjectPortable/test/spam_test1.txt")
        for link in links:
            site = FilteredDomainData(domain=link)
            filter.process_data(data=site, **param)

    def testSortList(self):
        anchorTextRows = []
        anchorTextRows.append(("tit", 10000, 2000, 1000))
        anchorTextRows.append(("man", 20000, 2000, 1000))
        anchorTextRows.append(("woman", 20000, 2000, 1000))
        anchorTextRows.append(("animal", 30000, 2000, 1000))
        anchorTexts = [x[0] for x in sorted(anchorTextRows, key=lambda anchorRow: anchorRow[1], reverse=True)]
        for anchor in anchorTexts:
            print(anchor)

    def testGetBacklinks(self):
        domain = "bufinserv.co.uk"
        max_count = 10
        niche = ""
        # niche = "Business/Financial Services"
        backlinks = majestic.get_backlinks(domain, max_count=max_count, topic=niche, is_dev=False)
        for item in backlinks:
            print(item)

    def testGetBackLinks2(self):
        logging_path = "/Users/superCat/Desktop/PycharmProjectPortable/Seeds/Gambling2.csv"
        FileHandler.create_file_if_not_exist(logging_path)
        Logging.CsvLogger.log_to_file_path(logging_path, [MajesticBacklinkDataStruct.get_tilte(), ])
        max_count = 100
        niche = "Games/Gambling"
        # niche = "Business/Financial Services"
        sites = GoogleCom.get_sites(keyword="gambling", index=0)
        backlinks = GoogleMajestic.get_sites_by_seed_sites(majestic, sites, catagories=niche, iteration=0, count_per_domain=max_count)
        for item in backlinks:
            if isinstance(item, MajesticBacklinkDataStruct):
                print(item)
                Logging.CsvLogger.log_to_file_path(logging_path, [item.to_tuple(), ])

    def testGetBackLinks3(self):
        file_path = "/Users/superCat/Desktop/PycharmProjectPortable/Seeds/GamblingSeed1.txt"
        sites = FileHandler.read_lines_from_file(file_path)
        logging_path = "/Users/superCat/Desktop/PycharmProjectPortable/Seeds/Gambling3.csv"
        FileHandler.create_file_if_not_exist(logging_path)
        # Logging.CsvLogger.log_to_file_path(logging_path, [MajesticBacklinkDataStruct.get_tilte(), ])
        max_count = 2000
        # niche = "Games/Gambling"
        # niche = "Business/Financial Services"
        niche = ""
        #sites = GoogleCom.get_sites(keyword="gambling", index=0)
        backlinks = GoogleMajestic.get_sites_by_seed_sites(majestic, sites, catagories=niche, iteration=0,
                                                           count_per_domain=max_count, callback=backlink_callback)
        # for item in backlinks:
        #     if isinstance(item, MajesticBacklinkDataStruct):
        #         print(item)
        #         Logging.CsvLogger.log_to_file_path(logging_path, [item.to_tuple(), ])

    def testCatagory(self):
        catagories = ["","Arts", "Arts/", "arts", "Arts/Movies", "Arts/Movie"]
        for item in catagories:
            try:
                print(CategoryManager.decode_sub_category(item))
            except Exception as ex:
                print(ex)

    def testCatagory2(self):
        import csv
        path = "/Users/superCat/Desktop/PycharmProjectPortable/test/17-09-2015-Good-Results.csv"
        counter = 0
        with open(path, mode='r', newline='') as csv_file:
            rd = csv.reader(csv_file, delimiter=',')
            for row in rd:
                if counter > 0:
                    parse_majestic_topic(row[10])

                counter += 1
                print("current loc:", counter)

    def testCategory3(self):
        save_path = "/Users/superCat/Desktop/PycharmProjectPortable/test/CategoryDB.db"
        manager = CategoryManager()
        db_manager = CategoryDBManager(save_path)
        for main_category in MainCategory.get_all_category():
            sub_categories = [SubCategory(main_category, item) for item in manager.get_sub_categories(main_category)]
            for item in sub_categories:
                db_manager.get_sub_category(item)
        db_manager.save()

        for item in db_manager.categories:
            if isinstance(item, Serializable):
                print(item.get_serializable(False))

    def testCatagory4(self):
        seed_db_addr = "/Users/superCat/Desktop/PycharmProjectPortable/Seeds/CategorySeedDB.db"
        category_db_addr = "/Users/superCat/Desktop/PycharmProjectPortable/test/CategoryDB.db"
        db = CategorySeedSiteDB(seed_db_addr)
        basic_manager = CategoryManager()
        category_manager = CategoryDBManager(category_db_addr)
        seed_manager = CategorySiteDBManager(db)
        import csv
        path = "/Users/superCat/Desktop/PycharmProjectPortable/Seeds/Gambling.csv"
        counter = 0
        with open(path, mode='r', newline='') as csv_file:
            rd = csv.reader(csv_file, delimiter=',')
            for row in rd:
                if len(row) == 6:
                    try:
                        domain, backlink, tf, cf, topic, topical_tf = row
                        if len(topic) > 0:
                            decoded_topic = basic_manager.decode_sub_category(topic, False)
                            data = MajesticBacklinkDataStruct(ref_domain=domain, src_cf=int(cf),
                                                              src_tf=int(tf), src_topic=str(decoded_topic), src_topical_tf=int(topical_tf))
                            seed_manager.append_to_buff(data=data, category=str(decoded_topic))
                    except Exception as ex:
                            print(ex)
                    finally:
                        counter += 1
                        print("current loc:", counter, "data:", row)
        seed_manager.close()

    def testGetSeedsFromBacklinks(self):
        logging_path = "/Users/superCat/Desktop/PycharmProjectPortable/Seeds/GeneralSeed.csv"
        seed_db_addr = "/Users/superCat/Desktop/PycharmProjectPortable/Seeds/CategorySeedDB.db"
        category_db_addr = "/Users/superCat/Desktop/PycharmProjectPortable/test/CategoryDB.db"
        db = CategorySeedSiteDB(seed_db_addr)
        basic_manager = CategoryManager()
        category_manager = CategoryDBManager(category_db_addr)
        seed_manager = CategorySiteDBManager(db)
        counter = 0

        def backlink_callback_inner(backlink: MajesticBacklinkDataStruct):
            if len(backlink.src_topic) > 0:
                decoded_topic = basic_manager.decode_sub_category(backlink.src_topic, False)
                # print(backlink)
                Logging.CsvLogger.log_to_file_path(logging_path, [backlink.to_tuple(), ])
                seed_manager.append_to_buff(data=backlink, category=str(decoded_topic))

        max_count = 2000
        total_count = 0
        niches = ["Home/Gardening",]
        forbidden_list = ["bbc.co.uk", "wikipedia.org", "youtube.com", ".edu", "amazon.co.uk", "facebook.com"]
        for niche in niches:
            decoded_topic = basic_manager.decode_sub_category(niche, True)
            print(decoded_topic)
        minimum_tf = 30
        # sites = GoogleCom.get_sites(keyword="Marketing and Advertising", index=0, filter_list=forbidden_list)[10:]
        sites = [x.ref_domain for x in db.get_from_table("Home/Gardening", 100, 200, {"TF": minimum_tf})]
        GoogleMajestic.get_sites_by_seed_sites(majestic, sites, catagories=niches, iteration=1,
                                                           count_per_domain=max_count, callback=backlink_callback_inner,
                                                           max_count=1000, tf=minimum_tf)
        seed_manager.close()
        # total_count += len(backlinks)
        # print("job finished, total backlinks:", total_count)

    def testPrintSeedDB(self):
        seed_db_addr = "/Users/superCat/Desktop/PycharmProjectPortable/Seeds/CategorySeedDB.db"
        db = CategorySeedSiteDB(seed_db_addr)
        seed_manager = CategorySiteDBManager(db)
        categories = db.get_sub_category_tables_name()
        total_count = 0
        target_niche = "Home/"
        for item in categories:
            if target_niche in item or len(target_niche) == 0:
                count = db.get_total(item)
                total_count += count
                print(item, "  ", count)
        print("total:", total_count)

    def testSeedExport(self):
        seed_db_addr = "/Users/superCat/Desktop/PycharmProjectPortable/sync/SeedSitesList"
        seed_db = SeedSiteDB("24/10/2015 Home", db_addr=seed_db_addr)

        categoy_db_addr = "/Users/superCat/Desktop/PycharmProjectPortable/Seeds/CategorySeedDB.db"
        db = CategorySeedSiteDB(categoy_db_addr)
        seed_manager = CategorySiteDBManager(db)
        categories = db.get_sub_category_tables_name()
        target_ca = [x for x in categories if "Home" in x and "Home/Gardening" not in x]
        sites = []
        seeds_needed = 20000
        percentage = 0.235
        for ca in target_ca:
            sites.clear()
            count = db.get_total(ca)
            if percentage == 1 and count > seeds_needed:
                count = seeds_needed
            count = int(percentage * count)
            if count > 0:
                temp = db.get_from_table(ca, 0, count)
                for item in temp:
                    if isinstance(item, MajesticBacklinkDataStruct):
                        sites.append((item.ref_domain, 0))
                seed_db.add_sites(sites, skip_check=True)



