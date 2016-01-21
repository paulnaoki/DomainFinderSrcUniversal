from urllib.parse import quote
import json
import requests
from multiprocessing.pool import ThreadPool
from DomainFinderSrc.Utilities.Proxy import ProxyStruct
import time
from DomainFinderSrc.Scrapers.SeedSiteGenSearchEngineInterface import *
import bs4
from DomainFinderSrc.Scrapers.WebRequestCommonHeader import WebRequestCommonHeader
from DomainFinderSrc.Scrapers.LinkChecker import LinkChecker


class BingConst:
    SearchKeyword = "http://api.bing.com/osjson.aspx?query={0:s}"
    SearchLink = "http://www.bing.com/search?&go=Submit&&form=QBRE&q={0:s}&pq={1:s}&first={2:d}&count={3:d}"
    SitePath = ".b_algo a"  # use CSS selector


class BingCom(SeedSiteGeneratorInterface):
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
            request_link = BingConst.SearchKeyword.format(quote(keyword),)
            if len(proxy_str) > 0:
                format_proxy = "http://"+proxy_str+"/"
                proxy = {
                    "http": format_proxy,  # "http://user:pass@10.10.1.10:3128/"
                }
                response = requests.get(request_link, timeout=5, proxies=proxy)
            else:
                response = requests.get(request_link, timeout=5)

            json_converted = json.loads(str(response.content, encoding="utf-8"))
            suggestions = json_converted[1]
            time.sleep(interval)
        except Exception as ex:
            print(ex)
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
        return [10, 20, 50]

    @staticmethod
    def get_proxy_arg(proxy: ProxyStruct):
        proxy_str = ""
        if isinstance(proxy, ProxyStruct):
            if len(proxy.user_name) > 0:
                proxy_str = "{0:s}:{1:s}@{2:s}:{3:d}".format(proxy.user_name, proxy.psd, proxy.addr, proxy.port)
            else:
                proxy_str = "{0:s}:{1:d}".format(proxy.addr, proxy.port)
        if len(proxy_str) > 0:
            return {
                "http": "http://"+proxy_str,  # "http://user:pass@10.10.1.10:3128"
                "https": "https://"+proxy_str,
            }
        else:
            return None

    @staticmethod
    def _get_response(request_link: str, proxy: ProxyStruct=None, timeout=5, user_agent=""):
        proxy_dict = BingCom.get_proxy_arg(proxy)
        headers = WebRequestCommonHeader.get_html_header(user_agent=user_agent)
        request_parameters = {
            "timeout": timeout,
            "headers": headers,
        }
        if isinstance(proxy_dict, dict):
            # request_parameters.update({"proxies": proxy_dict})
            return requests.get(request_link, proxies=proxy_dict, **request_parameters)
        else:
            return requests.get(request_link, **request_parameters)

    @staticmethod
    def get_sites(keyword: str, page_number: int=1, result_per_page: int=100,
                  index: int=0, length: int=100, use_browser=False,
                  source_type="", filter_list=[], country_code='', return_domain_home_only=True, days_ago=0,
                  **kwargs) -> []:

    # def get_sites(keyword: str, page: int=1, index: int=0, length: int=100,
    #               history=SeedSiteSettings.TIME_NOW, blog=False) -> []:
        assert page_number > 0, "page number should greater than 0"
        assert index >= 0, "index should greater or equal to 0"
        assert length > 0, "length should greater than 0"
        search_query = BingConst.SearchLink.format(quote(keyword), quote(keyword), (page_number-1)*length + index + 1, length)
        user_agent = WebRequestCommonHeader.webpage_agent
        try:
            req = BingCom._get_response(request_link=search_query, user_agent=user_agent, **kwargs)
            # req = requests.get(search_query, timeout=30, headers=WebRequestCommonHeader.get_html_header())
            result = req.text
            soup = bs4.BeautifulSoup(result)
            tags = soup.select(BingConst.SitePath)
            domains = []
            for tag in tags:
                try:
                    domain = tag.attrs["href"].strip().replace(" ", "")
                    if return_domain_home_only:
                        domain = LinkChecker.get_root_domain(domain, use_www=False)[2]  # get the link
                    else:
                        domain = LinkChecker.get_root_domain(domain, use_www=False)[3]
                    if len(domain) > 0:
                        domains.append(domain)
                except:
                    pass

            new_list = []
            if isinstance(domains, list):
                if len(filter_list) > 0:
                    for domain in domains:
                        if isinstance(domain, str):
                            temp = domain.lower().strip()
                            if not any(x in temp for x in filter_list):
                                new_list.append(temp)
                else:
                    new_list = domains

            end = index + length
            data_len = len(new_list)
            if domains is not None and index < data_len:
                if data_len >= end:
                    return new_list[index:end]
                else:
                    return new_list[index:]
            else:
                return []

        except Exception as ex:
            print(ex)
            return None