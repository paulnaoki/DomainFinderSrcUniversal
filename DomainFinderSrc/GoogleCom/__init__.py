from urllib.parse import quote
import bs4
import requests
from selenium import webdriver
from DomainFinderSrc.Scrapers.WebRequestCommonHeader import WebRequestCommonHeader
from DomainFinderSrc.Scrapers.LinkChecker import LinkChecker
from multiprocessing.pool import ThreadPool
from DomainFinderSrc.Utilities.Proxy import ProxyStruct
import time
from DomainFinderSrc.Scrapers.SeedSiteGenSearchEngineInterface import *
import warnings


class GoogleUtility:
    CountryCodeEnglish = ["uk", "us", "gb", "au", "nz", "nl", "za", "ca", "ie"]

    @staticmethod
    def get_supported_country_code():
        return GoogleUtility.CountryCodeEnglish

    @staticmethod
    def get_local_endpoint(country_code: str, sub_domain="www") -> str:
        if country_code is None or country_code not in GoogleUtility.get_supported_country_code():
            raise LookupError("wrong country code given, should be either: " + str(GoogleUtility.get_supported_country_code()))
        else:
            end_point_format = "https://{0:s}.google.".format(sub_domain,)
            suffix = {
                "gb": "co.uk",
                "us": "com",
                "au": "com.au",
                "nz": "co.nz",
                "nl": "nl",
                "za": "co.za",
                "ca": "ca",
                "ie": "ie",
            }.get(country_code.lower(), "com")
            return end_point_format+suffix

    @staticmethod
    def get_query_for_days(days_ago: int) -> str:
        days_query = ""
        if days_ago > 0:
            # replace 'd'for day with 'w', 'm', 'y' for week, month, year respectively
            days_query = "&as_qdr=d{0:d}".format(days_ago,)
        return days_query

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


class GoogleConst:
    CommonSearchPath = "/search?q={0:s}&num={1:d}&start={2:d}&gl={3:s}&gws_rd=cr"
    SearchKeywordPath = "/complete/search?output=toolbar&hl=en&format=firefox&q={0:s}&gl={1:s}&gws_rd=cr"
    # SearchLink = "https://www.google.com/search?q=%s&num=%d&start=%d"
    # SearchKeyword = "http://suggestqueries.google.com/complete/search?output=toolbar&hl=en&format=firefox&q={0:s}"
    # SitePath = "._Rm"  # use CSS selector
    SitePath = "cite"
    Result100 = 100
    Result50 = 50
    Result20 = 20
    Result10 = 10

    SourceTypeBlog = "Blog"
    SourceTypeNews = "News"
    SourceTypeWeb = "Web"


class GoogleCom(SeedSiteGeneratorInterface):

    @staticmethod
    def _get_response(request_link: str, proxy: ProxyStruct=None, timeout=5, user_agent=""):
        proxy_dict = GoogleUtility.get_proxy_arg(proxy)
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
    def _get_response_browser(request_link: str, proxy: ProxyStruct=None, timeout=5, user_agent=""):
        chrome_options = webdriver.ChromeOptions()
        if proxy is not None:
            PROXY = proxy.str_no_auth()
            if len(proxy.user_name) > 0:
                warnings.warn("GoogleCom._get_response_browser(): proxy constructed without username and password, might not work on other machines.")
            chrome_options.add_argument('--proxy-server=http://{0:s}'.format(PROXY,))
        if len(user_agent) > 0:
            chrome_options.add_argument('--user-agent={0:s}'.format(user_agent,))
        chrome = webdriver.Chrome(chrome_options=chrome_options)
        chrome.set_page_load_timeout(timeout)
        try:
            chrome.get(request_link)
            inner_text = chrome.page_source
        except Exception as ex:
            print(ex)
            inner_text = None
        finally:
            chrome.close()
        return inner_text



    @staticmethod
    def get_search_results(keyword: str, page_number: int, proxy: ProxyStruct=None, result_per_page: int=GoogleConst.Result100, timeout=5,
                           return_domain_home_only=True, use_forbidden_filter=True, days_ago=0, addtional_query_parameter: str="",
                           country_code="us", use_browser=False) -> list:
        """
        generic normal search, get a list of domains form page
        :param keyword:
        :param page_number:  > 0
        :param resultPerPage:
        :param timeout:
        :param return_domain_home_only: return root domain name if True, else return protocol suffix + domain name
        :param use_forbidden_filter:
        :param days_ago: specify how many days ago before when results were indexed.
        :return:
        """
        assert page_number > 0, "page number should be greater than 0."
        page_range = GoogleCom.get_result_per_page_range()
        assert result_per_page in page_range, "result per page should be one of those values:" + str(page_range)

        sub_domain = "www"
        request_link = GoogleUtility.get_local_endpoint(country_code, sub_domain) \
                       + GoogleConst.CommonSearchPath.format(quote(keyword), result_per_page, (page_number - 1) * result_per_page, country_code) \
                       + addtional_query_parameter+GoogleUtility.get_query_for_days(days_ago)
        try:
            user_agent = WebRequestCommonHeader.webpage_agent
            if not use_browser:
                response = GoogleCom._get_response(request_link, proxy=proxy, timeout=timeout, user_agent=user_agent)
                if not response.status_code == 200:
                    # if response.status_code == 503:
                        # print(response.text)
                    raise ConnectionRefusedError("error getting result, with status code:", response.status_code)
                result = response.text
            else:
                result = GoogleCom._get_response_browser(request_link, proxy=proxy, timeout=timeout, user_agent=user_agent)
            soup = bs4.BeautifulSoup(result)
            tags = soup.select(GoogleConst.SitePath)
            domains = []
            for tag in tags:
                try:
                    domain = tag.text.strip().replace(" ", "")
                    if return_domain_home_only:
                        domain = LinkChecker.get_root_domain(domain, use_www=False)[2]  # get the link
                    else:
                        domain = LinkChecker.get_root_domain(domain, use_www=False)[3]
                    if use_forbidden_filter and LinkChecker.is_domain_forbidden(domain):
                        continue
                    if len(domain) > 0:
                        domains.append(domain)
                except:
                    pass
            return domains

        except Exception as ex:
            print(ex)
            return None

    @staticmethod
    def _get_suggestion(keyword="", proxy: ProxyStruct=None, timeout=5, country_code="us") -> list:
        suggestions = []
        try:
            # only US endpoint works.
            request_link = GoogleUtility.get_local_endpoint(country_code="us", sub_domain="suggestqueries")\
                           + GoogleConst.SearchKeywordPath.format(quote(keyword), country_code,)
                           # + GoogleUtility.get_query_for_days(days_ago)

            response = GoogleCom._get_response(request_link, proxy=proxy, timeout=timeout)
            soup_xml = bs4.BeautifulSoup(response.text)
            anchors = soup_xml.find_all("suggestion")
            for anchor in anchors:
                if anchor.has_attr("data"):
                    link = anchor["data"]
                    suggestions.append(link)
            # time.sleep(interval)
        except Exception as ex:
            print("error in: ", keyword, " msg: ", ex)
        finally:
            return suggestions

    @staticmethod
    def get_suggestion(keywords: [], proxies: [], interval=2) -> []:
        proxies_len = len(proxies)
        if proxies_len == 0:
            proxies_len = 1
        pool = ThreadPool(processes=proxies_len)

    @staticmethod
    def get_result_per_page_range()-> list:
        """
        get maximum number of results per search query in a range of numbers. e.g: [10,20,50,100]
        :return: a list of available numbers
        """
        return [10, 20, 50, 100]

    @staticmethod
    def get_sites(keyword: str, page_number: int=1, result_per_page: int=GoogleConst.Result100,
                  index: int=0, length: int=100,
                  source_type=GoogleConst.SourceTypeWeb, filter_list=[],
                  **kwargs) -> []:
        # history=SeedSiteSettings.TIME_NOW,
        assert length <= result_per_page, "return data length should be <= total results in a page."

        if source_type == GoogleConst.SourceTypeBlog:
            addtional_args = "&site=webhp&tbm=blg&source=lnt"
        elif source_type == GoogleConst.SourceTypeWeb:
            addtional_args = ""
        else:
            raise ValueError("unsupported source type.")

        domains = GoogleCom.get_search_results(keyword=keyword, page_number=page_number, result_per_page=result_per_page,
                                               addtional_query_parameter=addtional_args, **kwargs)
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