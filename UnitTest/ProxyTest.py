from DomainFinderSrc.Scrapers.WebRequestCommonHeader import WebRequestCommonHeader
from DomainFinderSrc.Utilities.Proxy import ProxyStruct

__author__ = 'Paulli'
from DomainFinderSrc.BuyProxyOrg import BuyProxyOrg
from unittest import TestCase
from UnitTest.Accounts import buy_proxy_org_account
from DomainFinderSrc.GoogleCom import GoogleCom, GoogleConst, GoogleUtility
import time
from DomainFinderSrc.Scrapers.WebDriver import WebDriver
from selenium import webdriver


class ProxyTester(TestCase):

    def testGetLlinks(self, keyword="law", page_number=1, index=0, length=100, country_code="us",
                      source_type=GoogleConst.SourceTypeWeb, days_ago=10, proxy=None):
        sites = GoogleCom.get_sites(keyword, page_number=page_number, index=index, length=length,
                                    country_code=country_code, source_type=source_type, days_ago=days_ago,
                                    return_domain_home_only=False, proxy=proxy)
        for item in sites:
            print(item)
        return sites

    def testProxyGet(self):
        proxy = BuyProxyOrg(buy_proxy_org_account)
        proxy_list = proxy.get_proxies(5)
        for item in proxy_list:
            print("try proxy:", item)
            # sites = self.testGetLlinks(proxy=item)
            # for site in sites:
            #     print(site)
            time.sleep(1)

    def testProxyGetOpen(self):

        request_url = "https://www.google.com/search?q=crimial%20law&num=100&start=0&site=webhp&tbm=blg&source=lnt&as_qdr=y5"
        # request_url = "https://www.whatismyip.com/"
        proxy = BuyProxyOrg(buy_proxy_org_account)
        proxy_list = proxy.get_proxies(5)

        for item in proxy_list:
            PROXY = item.str_no_auth()
            print("try proxy:", str(item))
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--proxy-server=http://%s' % PROXY)

            chrome = webdriver.Chrome(chrome_options=chrome_options)
            # driver = WebDriver.get_chrome(additional_options=chrome_options)
            chrome.get(request_url)
            # sites = self.testGetLlinks(proxy=item)
            # for site in sites:
            #     print(site)
            time.sleep(5)

    def testRequest(self):
        request_link = "https://www.atagar.com/echo.php"
        proxy = ProxyStruct(addr="192.227.162.44", port=80, user_name="sudo", psd="goodlife")
        result = GoogleCom._get_response(request_link, proxy=proxy)
        print(result.text)

    def testOllipldsfapenChrome(self):
        '''
        todo:http://stackoverflow.com/questions/29983106/how-can-i-set-proxy-with-authentication-in-selenium-chrome-web-driver-using-pyth
        :return:
        '''
        # request_url = "https://www.google.com/search?q=crimial%20law&num=100&start=0&site=webhp&tbm=blg&source=lnt&as_qdr=y5"
        request_url = "https://www.google.com/search?q=bbs&num=100&start=0&gl=us&gws_rd=cr&as_qdr=d10"
        # request_url = "https://www.whatismyip.com/"
        # request_url = "http://whatsmyuseragent.com/"
        proxy = BuyProxyOrg(buy_proxy_org_account)
        proxy_list = proxy.get_proxies(5)
        chrome_list = list()
        for item in proxy_list:
            PROXY = item.str_no_auth()
            chrome_options = webdriver.ChromeOptions()
            # PROXY = "23.95.32.92:80"
            # USER_AGENT = "i like ice cream."

            USER_AGENT = WebRequestCommonHeader.webpage_agent
            chrome_options.add_argument('--proxy-server=http://{0:s}'.format(PROXY,))
            chrome_options.add_argument('--user-agent={0:s}'.format(USER_AGENT,))
            chrome = webdriver.Chrome(chrome_options=chrome_options)
            chrome.get(request_url)
            chrome_list.append(chrome)
        time.sleep(60)
        for item in chrome_list:
            item.close()
        # chrome.close()
