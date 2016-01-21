from DomainFinderSrc.BuyProxyOrg import BuyProxyOrg
from UnitTest.Accounts import buy_proxy_org_account
from unittest import TestCase
from DomainFinderSrc.BingCom import *
from DomainFinderSrc.Scrapers.LinkChecker import *

from urllib import request
import csv
from io import StringIO
from pysimplesoap.client import SoapClient


filter_list = ["wikipedia.", ".youtube.", ".edu", ".gov", "wsj.com", "nytimes.com", "forbes.com",
               "intel.com", "twitter.com", "google.", "facebook.", "weibo.", "sina.", "yahoo.", "usnews.com",
               "bbc.", "ac.uk", "thetimes.", "newrepublic.com", "theguardian.com", "newyorker.com", "newadvent.org",
               "telegraph.co.uk", ]


class OnlineFileReader:
    @staticmethod
    def read_csv_file(link: str) -> []:
        response = request.urlopen(link)
        f = StringIO(response.read().decode('utf-8'))
        rowList = f.readlines()
        csv_f = csv.reader(rowList, delimiter="\t")
        # columns = [0]
        dataSize = len(rowList)
        resultList = []
        counter = 0
        if dataSize > 1:
            for row in csv_f:
                if counter > 0:
                    resultList.append(row[0])
                counter += 1
            return resultList
        else:
            return None


class BingTest(TestCase):
    def testBingResult(self):
        keyword = "law blog"
        proxy_site = BuyProxyOrg(buy_proxy_org_account)
        proxies = proxy_site.get_proxies(timeout=5)
        sites = BingCom.get_sites(keyword, page_number=1, index=0, length=100, filter_list=filter_list,
                                    country_code="us", source_type="", days_ago=10,
                                    return_domain_home_only=False, proxy=proxies[0], timeout=30)
        for item in sites:
            print(item)
        return sites

    def testBacklinksData(self):
        testURL = "https://wmstat.bing.com/webmaster/data.ashx?wmkt=en-US&wlang=en-US&type=linkexplorer&linkurl=http://susodigital.com&url=" \
                  "&anchor=&query=&domain=true&source=1"

        client = SoapClient(wsdl="https://ssl.bing.com/webmaster/api.svc?wsdl")
        print(client)
