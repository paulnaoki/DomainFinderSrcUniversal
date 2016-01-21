from DomainFinderSrc.Utilities.Proxy import ProxyStruct
from unittest import TestCase
from DomainFinderSrc.GoogleCom import GoogleCom, GoogleConst, GoogleUtility
from DomainFinderSrc.BingCom import BingCom
import random
import time
from DomainFinderSrc.MiniServer.Common.DBInterface import *
from DomainFinderSrc.Utilities.FileIO import FileHandler
from DomainFinderSrc.BuyProxyOrg import BuyProxyOrg
from UnitTest.Accounts import buy_proxy_org_account


filter_list = ["wikipedia.", ".youtube.", ".edu", ".gov", "wsj.com", "nytimes.com", "forbes.com",
               "intel.com", "twitter.com", "google.", "facebook.", "weibo.", "sina.", "yahoo.", "usnews.com",
               "bbc.", "ac.uk", "thetimes.", "newrepublic.com", "theguardian.com", "newyorker.com", "newadvent.org",
               "telegraph.co.uk", ]


class GoogleTest(TestCase):
    def test_in(self):
        domains= ['http://avalon.law.yale.edu',
                'http://www.vermontlaw.edu']
        for domain in domains:
            if isinstance(domain, str):
                temp = domain.lower().strip()
                if not any(x in temp for x in filter_list):
                    print(temp)

    def testGetLlinks(self, keyword="law", page_number=1, index=0, length=100, country_code="us",
                      source_type=GoogleConst.SourceTypeWeb, days_ago=10, proxy=None, use_browser=True):
        if proxy is None:
            proxy = ProxyStruct(addr="192.227.162.44", port=80)
        # sites = GoogleCom.get_sites(keyword, page_number=page_number, index=index, length=length, filter_list=filter_list,
        #                             country_code=country_code, source_type=source_type, days_ago=days_ago,
        #                             return_domain_home_only=False, proxy=proxy, use_browser=use_browser, timeout=30)
        sites = BingCom.get_sites(keyword, page_number=page_number, index=index, length=length, filter_list=filter_list,
                                    country_code=country_code, source_type=source_type, days_ago=days_ago,
                                    return_domain_home_only=False, proxy=proxy, use_browser=use_browser, timeout=30)
        for item in sites:
            print(item)
        return sites

    def test_range(self):
        for i in range(1, 2):
            print(i)

    def testGetLinksBatch_single_t(self, niche="Society/Law", keywords=["lawyer", "legal cases"], page_count=5,
                                   index=0, length=100, country_code="us", source_type=GoogleConst.SourceTypeWeb, days_ago=0,
                                   min_delay=2, max_delay=5, proxies=None, use_browser=True):
        assert page_count >= 1, "number of page must be greater or equal to 1."
        db_path = "/Users/superCat/Desktop/PycharmProjectPortable/Seeds/BlogSeedDB.db"
        db = SeedSiteDB(table=niche, db_addr=db_path)
        proxy_counter = 0
        for keyword in keywords:
            for page in range(1, page_count+1):
                proxy = None
                if isinstance(proxies, list):
                    print("cuurent proxy counter:", proxy_counter, " proxy len:", len(proxies))
                    if proxy_counter >= len(proxies):
                        proxy_counter = 0
                        print("reset proxy counter:", proxy_counter)
                    proxy = proxies[proxy_counter]

                try:
                    if proxy is not None:
                        links = self.testGetLlinks(keyword, page_number=page, index=index, length=length,
                                                   country_code=country_code, source_type=source_type,
                                                   days_ago=days_ago, proxy=proxy, use_browser=use_browser)
                    else:
                        links = self.testGetLlinks(keyword, page_number=page, index=index, length=length,
                                                   country_code=country_code, source_type=source_type,
                                                   days_ago=days_ago, use_browser=use_browser)
                    if isinstance(links, list):
                        print("keyword: ", keyword, " page number: ", page, " adding seeds:", len(links))
                        db.add_sites(links, skip_check=False)
                except Exception as ex:
                    print("testGetLinksBatch_single_t()", ex)
                finally:
                    proxy_counter += 1
                    interval = random.randint(min_delay, max_delay)
                    time.sleep(interval)
        db.close()

    def testGetSuggestion(self, keyword: str="law case", proxy=None, country_code="gb"):
        suggestions = GoogleCom._get_suggestion(keyword, proxy=proxy, country_code=country_code)
        print("doing keyword:", keyword, " with proxy:", str(proxy))
        for item in suggestions:
            print(item)
        return suggestions

    def testGetSuggestionBatch(self, keywords: list=[], proxies=None, country_code="us", min_delay=15, max_delay=60, callback=None):
        return_list = list()
        proxy_counter = 0
        for item in keywords:
            proxy = None
            if isinstance(proxies, list):
                if proxy_counter >= len(proxies):
                    proxy_counter = 0
                proxy = proxies[proxy_counter]
            try:
                if proxy is not None:
                    temp = self.testGetSuggestion(keyword=item, proxy=proxy, country_code=country_code)
                else:
                    temp = self.testGetSuggestion(keyword=item, country_code=country_code)
                if temp is not None:
                    return_list += temp
                    if callback is not None:
                        callback(temp)
            except Exception as ex:
                print(ex)
            finally:
                proxy_counter += 1
                interval = random.randint(min_delay, max_delay)
                time.sleep(interval)
        return list(set(return_list))

    def testGetkeywordsRecursive(self, niche="Society/Law", level=1, keyword_init=[],
                                 proxies=None, country_code="us", min_delay=2, max_delay=5, offset=120):
        keyword_log_path = "/Users/superCat/Desktop/PycharmProjectPortable/Seeds/KeywordSuggestions/"+niche.replace('/', '-')+".txt"

        def save_callback(keywords: list):
            FileHandler.append_lines_to_file(keyword_log_path, keywords, option="at")

        if len(keyword_init) == 0:
            keyword_init = list(set(FileHandler.read_lines_from_file(keyword_log_path)))[offset:]
            for item in keyword_init:
                print(item)
            print("total keywords:", len(keyword_init))
        if proxies is None:
            proxy_site = BuyProxyOrg(buy_proxy_org_account)
            proxies = proxy_site.get_proxies(timeout=5)
        current_level = 0
        keywords_pool = keyword_init
        while current_level < level:
            keyword_init = self.testGetSuggestionBatch(keyword_init, proxies=proxies, country_code=country_code,
                                                       min_delay=min_delay, max_delay=max_delay, callback=save_callback)
            keywords_pool += keyword_init
            current_level += 1
        FileHandler.remove_file_if_exist(keyword_log_path)
        FileHandler.append_lines_to_file(keyword_log_path, keywords_pool, option="t")

    def testGetBlogs(self):
        niche = "Society/Law"
        proxy_site = BuyProxyOrg(buy_proxy_org_account)
        proxies = proxy_site.get_proxies(timeout=5)
        keyword_log_path = "/Users/superCat/Desktop/PycharmProjectPortable/Seeds/KeywordSuggestions/"+niche.replace('/', '-')+".txt"
        # countries = GoogleUtility.CountryCodeEnglish
        countries = ["uk", ]
        min_delay = 2
        max_delay = 5
        max_page = 2
        days_ago = 4*365
        target_keywords_init = ["legal case", "Labour law", "human rights law", "crime law", "Immigration law",
                                "Family law", "Transactional law", "Company law", "Commercial law", "Admiralty law",
                                "Intellectual property law", "international law", "tax law", "banking law", "competition law",
                                "consumer law", "environmental law"]
        suggested_keywords = []
        for country in countries:
            # temp_keywords = self.testGetSuggestionBatch(target_keywords_init, proxies=proxies,
            #                                                   country_code=country,
            #                                                   min_delay=min_delay, max_delay=max_delay)
            temp_keywords = list(set(FileHandler.read_lines_from_file(keyword_log_path)))
            # FileHandler.append_lines_to_file(keyword_log_path, temp_keywords, option="at")
            # suggested_keywords += temp_keywords
            crawl_keywords = [x for x in list(set(target_keywords_init + temp_keywords))]
            self.testGetLinksBatch_single_t(niche, keywords=crawl_keywords, page_count=max_page, index=0, length=100,
                                            country_code=country, source_type=GoogleConst.SourceTypeBlog,
                                            min_delay=min_delay, max_delay=max_delay, days_ago=days_ago,
                                            proxies=proxies, use_browser=False)
        # all_keywords = list(set(target_keywords_init + suggested_keywords))
        # FileHandler.append_lines_to_file(keyword_log_path, all_keywords, option="xt")  # rewrite the keyword list for the record




