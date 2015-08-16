from urllib.parse import quote
import bs4
import requests
from DomainFinderSrc.Scrapers.WebRequestCommonHeader import WebRequestCommonHeader
from DomainFinderSrc.Scrapers.LinkChecker import LinkChecker
from multiprocessing.pool import ThreadPool
from DomainFinderSrc.Utilities.Proxy import ProxyStruct
import time
from DomainFinderSrc.Scrapers.SeekSiteGenerator import *


class GoogleConst:
    SearchLink = "https://www.google.com/search?q=%s&num=%d&start=%d"
    SearchKeyword = "http://suggestqueries.google.com/complete/search?output=toolbar&hl=en&format=firefox&q={0:s}"
    SitePath = "._Rm"  # use CSS selector
    Result100 = 100
    Result50 = 50
    Result20 = 20
    Result10 = 10


class GoogleCom(SeedSiteGeneratorInterface):

    @staticmethod
    def get_search_results(keyword: str, page_number: int, resultPerPage: int=GoogleConst.Result100, timeout=5,
                           return_domain_home_only=True, use_forbidden_filter=True, addtional_query_parameter: str="") ->[]:
        """
        generic normal search, get a list of domains form page
        :param keyword:
        :param page_number:  > 0
        :param resultPerPage:
        :param timeout:
        :param return_domain_home_only:
        :param use_forbidden_filter:
        :return:
        """
        prefix = "www."
        search_query = (GoogleConst.SearchLink + addtional_query_parameter) % (quote(keyword), resultPerPage, (page_number - 1) * resultPerPage)
        try:
            req = requests.get(search_query, timeout=timeout, headers=WebRequestCommonHeader.get_html_header())
            result = req.text
            soup = bs4.BeautifulSoup(result)
            tags = soup.select(GoogleConst.SitePath)
            domains = []
            for tag in tags:
                try:
                    domain = tag.text.strip().replace(" ", "")
                    if return_domain_home_only:
                        domain = LinkChecker.get_root_domain(domain)[2] #get the link
                    else:
                        domain = LinkChecker.get_root_domain(domain)[3]
                    if use_forbidden_filter and LinkChecker.is_domain_forbidden(domain):
                        continue
                    if len(domain) > 0:
                        domains.append(domain)
                except:
                    pass
            return domains

        except:
            return None

    @staticmethod
    def get_blogs(keyword: str, page_number: int, resultPerPage: int=GoogleConst.Result100, timeout=5,
                           return_domain_home_only=True, use_forbidden_filter=True):
        return GoogleCom.get_search_results(keyword, page_number, resultPerPage, timeout, return_domain_home_only, use_forbidden_filter,
                                            addtional_query_parameter="&site=webhp&tbm=blg&source=lnt")

    @staticmethod
    def _get_suggestion(keyword_proxy_pair: tuple) -> []:
        suggestions = []
        try:
            keyword = keyword_proxy_pair[0]
            proxy = keyword_proxy_pair[1]
            interval = keyword_proxy_pair[2]
            proxy_str = ""
            if isinstance(proxy, ProxyStruct):
                if len(proxy.user_name) > 0:
                    proxy_str = "{0:s}:{1:s}@{2:s}:{3:d}".format(proxy.user_name, proxy.psd, proxy.addr, proxy.port)
                else:
                    proxy_str = "{0:s}:{1:d}".format(proxy.addr, proxy.port)
            request_link = GoogleConst.SearchKeyword.format(quote(keyword),)
            if len(proxy_str) > 0:
                format_proxy = "http://"+proxy_str+"/"
                proxy = {
                    "http": format_proxy,  # "http://user:pass@10.10.1.10:3128/"
                }
                response = requests.get(request_link, timeout=5, proxies=proxy)
            else:
                response = requests.get(request_link, timeout=5)

            soup_xml = bs4.BeautifulSoup(response.text)
            anchors = soup_xml.find_all("suggestion")
            for anchor in anchors:
                if anchor.has_attr("data"):
                    link = anchor["data"]
                    suggestions.append(link)
            time.sleep(interval)
        except:
            pass
        finally:
            return suggestions

    @staticmethod
    def get_suggestion(keywords: [], proxies: [], interval=2) -> []:
        proxies_len = len(proxies)
        if proxies_len == 0:
            proxies_len = 1
        pool = ThreadPool(processes=proxies_len)

    @staticmethod
    def get_result_per_page_range()-> []:
        """
        get maximum number of results per search query in a range of numbers. e.g: [10,20,50,100]
        :return: a list of available numbers
        """
        return [10, 20, 50, 100]

    @staticmethod
    def get_sites(keyword: str, page: int=1, index: int=0, length: int=100,
                  history=SeedSiteSettings.TIME_NOW, blog=False) -> []:
        if blog:
            domains = GoogleCom.get_blogs(keyword, page, return_domain_home_only=False, timeout=30)
        else:
            domains = GoogleCom.get_search_results(keyword, page, return_domain_home_only=False, timeout=30)
        end = index + length
        data_len = len(domains)
        if domains is not None and index < data_len:
            if data_len >= end:
                return domains[index:end]
            else:
                return domains[index:]
        else:
            return []