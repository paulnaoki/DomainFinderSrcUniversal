import json
from urllib.parse import urlencode
from multiprocessing import pool
import requests
from DomainFinderSrc.ArchiveOrg import ArchiveStruct, ArchiveDetail
from DomainFinderSrc.Scrapers.LinkChecker import LinkChecker
from DomainFinderSrc.ArchiveOrg.ArchiveExplore import LinkUtility
from datetime import datetime


def test_response(link: str) -> (bool, str):
    # link_cls, ext = LinkUtility.get_link_class(link)
    status_code, content_type = LinkChecker.get_response(link)
    link_cls, ext = LinkUtility.get_link_class(link.rstrip('/'))
    # print("checking link:", link, " link cls:", link_cls, " ext:", ext)
    # if "image" in content_type:
    #     link_cls = LinkUtility.EXT_WEBPAGE
    # elif "html" in content_type:
    #     link_cls = LinkUtility.EXT_WEBPAGE
    # elif "css" in content_type:
    #     link_cls = LinkUtility.EXT_CSS
    # elif "javascript" in content_type:
    #     link_cls = LinkUtility.EXT_JS
    # else:
    #     link_cls = LinkUtility.EXT_OTHER

    if status_code != 200:
        # print(link, "status bad:", status_code, " content: ", content_type)
        return False, link_cls
    else:
        # print(link, "status good:", status_code, " content: ", content_type)
        return True, link_cls


class ArchiveOrg:

    BASE_QUERY_URL = "http://web.archive.org/cdx/search/cdx?"
    BASE_ARCHIVE_URL = "http://web.archive.org/web/"
    @staticmethod
    def get_url_info(link: str, min_size: int, limit: int=-500) ->[]:
        """
        get information about a link
        :param link: the html webpage link in archive
        :param min_size: minimum data length of the file from the link in Kb
        :param limit: number of returning results, positive counting from the begining, negative from the ending.
        :return: A list of archives of the link in ArchiveStruct format, newest first.
        """
        # http://web.archive.org/cdx/search/cdx?url=susodigital.com&output=json
        # &filter=statuscode:200&filter=mimetype:text/html&filter=!length:^([0-9]|[1-9][0-9]|[1-9][0-9][0-9]|[1-2][0-9][0-9][0-9])
        # $&collapse=digest&limit=500&matchType=exact&fl=timestamp,length,original
        if len(link) == 0:
            return []
        # if limit < 1:
        #     limit = 1
        if min_size > 1:
            size_query = "!length:^([0-9]|[1-9][0-9]|[1-9][0-9][0-9]|[1-{0:d}][0-9][0-9][0-9])$".format(min_size-1)
        else:
            size_query = "!length:^([0-9]|[1-9][0-9]|[1-9][0-9][0-9])$"
        archive_dict = {'url': link, 'filter': size_query, 'limit': limit, 'output': 'json',
                        'fl': 'timestamp,length,original', 'collapse': 'digest'}
        first_part = urlencode(archive_dict)
        second_part = urlencode((('filter', 'statuscode:200'), ('filter', 'mimetype:text/html')))
        query = first_part + "&" + second_part
        data = requests.get(ArchiveOrg.BASE_QUERY_URL+query)
        # jsoned = json.loads(str(data.content, encoding="utf-8"))
        jsoned = json.loads(data.text)
        data_len = len(jsoned) - 1
        if data_len > 0:
            result = []
            for time_stamp, length, original_link in jsoned[:-data_len-1:-1]:
                result.append(ArchiveStruct(link=original_link, date_stamp=time_stamp, size=length))
            return result  # newest first
        else:
            return []

    @staticmethod
    def get_domain_urls(link: str, limit: int=2000) ->[]:
        archive_dict = {'url': link, 'limit': limit, 'output': 'json', 'matchType': 'domain',
                        'fl': 'timestamp,length,original', 'collapse': 'urlkey'}
        query = urlencode(archive_dict)
        data = requests.get(ArchiveOrg.BASE_QUERY_URL+query)
        # jsoned = json.loads(str(data.content, encoding="utf-8"))
        jsoned = json.loads(data.text)
        data_len = len(jsoned) - 1
        if data_len > 0:
            result = []
            for time_stamp, length, original_link in jsoned:
                result.append(ArchiveStruct(link=original_link, date_stamp=time_stamp, size=length))
            return result  # newest first
        else:
            return []

    @staticmethod
    def get_archive_link(archive_struct: ArchiveStruct):
        if archive_struct is None:
            return ""
        if not archive_struct.link.endswith("/"):
            archive_struct.link += "/"
        return ArchiveOrg.BASE_ARCHIVE_URL + archive_struct.date_stamp + "/" + archive_struct.link

    @staticmethod
    def _get_archive_lang(archive: ArchiveStruct) -> str:
        link = ArchiveOrg.get_archive_link(archive)


    @staticmethod
    def get_archives_lang(root_domain: str, thread_size=10, profile_check=300) -> list:
        url = LinkChecker.get_valid_link(root_domain, link="")
        profiles = ArchiveOrg.get_url_info(url, min_size=1, limit=0-profile_check)
        today_stamp = datetime.utcnow().timestamp()
        for item in profiles:
            if isinstance(item, ArchiveStruct):
                timestamp = item.get_datestamp_unix_time()
                print(str(item), " converted:", str(timestamp))
        return []

    @staticmethod
    def get_best_archive(root_domain: str, thread_size=100, profile_check=10, pass_threshold=0.8, res_limit=2000) -> ArchiveDetail:
        """
        get the best profile from archive.org by doing profile spectrum analysis, given a root domain name.
        spectrum analysis: comparison between resources of current profile to all historic resources.
        :param root_domain: root domain in str, e.g: "google.co.uk"
        :param thread_size: number of thread to check resource link simultaneously
        :param profile_check: max number of profile to check
        :param pass_threshold: threshold define if a profile is good enough.
        :param res_limit: number of resource links in domain resource spectrum, including css, js, html etc.
        :return: tuple (archive in ArchiveStruct, spectrum value)
        """
        url = LinkChecker.get_valid_link(root_domain, link="")
        profiles = ArchiveOrg.get_url_info(url, min_size=1, limit=-profile_check)
        timestamp =""
        info = ArchiveOrg.get_domain_urls(url, limit=res_limit)
        res_count = len(info)
        archive = None
        current_rate = 0.0
        min_broken_res_count = 0
        good_rate_web_page = 0
        good_rate_image = 0
        good_rate_css = 0
        good_rate_js = 0
        good_rate_other = 0

        total_web_page_min = 0
        total_js_min = 0
        total_css_min = 0
        total_image_min = 0
        total_other_min = 0
        if res_count > 0:
            for profile in profiles:
                if isinstance(profile, ArchiveStruct):
                    total_web_page = 0
                    total_js = 0
                    total_css = 0
                    total_image = 0
                    total_other = 0

                    broken_web_page = 0
                    broken_js = 0
                    broken_css = 0
                    broken_image = 0
                    broken_other = 0

                    test_pool = pool.ThreadPool(processes=thread_size)
                    timestamp = profile.date_stamp
                    print("checking:", str(profile))
                    links = []
                    for item in info:
                        item.date_stamp = timestamp
                        links.append(ArchiveOrg.get_archive_link(item))
                    results = [test_pool.apply_async(func=test_response, args=(x,)) for x in links]
                    returned = [y.get() for y in results]
                    test_pool.terminate()
                    for result_good, link_cls in returned:
                        if link_cls == LinkUtility.EXT_WEBPAGE:
                            total_web_page += 1
                            if not result_good:
                                broken_web_page += 1
                        elif link_cls == LinkUtility.EXT_CSS:
                            total_css += 1
                            if not result_good:
                                broken_css += 1
                        elif link_cls == LinkUtility.EXT_JS:
                            total_js += 1
                            if not result_good:
                                broken_js += 1
                        elif link_cls == LinkUtility.EXT_IMAGE:
                            total_image += 1
                            if not result_good:
                                broken_image += 1
                        else:
                            total_other += 1
                            if not result_good:
                                broken_other += 1
                    broken_res_count = broken_image + broken_other + broken_web_page + broken_js + broken_image
                    passed = False
                    total_broken_rate = 1-broken_res_count/res_count
                    if total_broken_rate >= pass_threshold:
                        passed = True
                    if total_broken_rate > current_rate:
                        current_rate = total_broken_rate
                        archive = profile
                        good_rate_web_page = 0 if total_web_page == 0 else 1 - broken_web_page/total_web_page
                        good_rate_image = 0 if total_image == 0 else 1 - broken_image/total_image
                        good_rate_css = 0 if total_css == 0 else 1 - broken_css/total_css
                        good_rate_js = 0 if total_js == 0 else 1 - broken_js/total_js
                        good_rate_other = 0 if total_other == 0 else 1 - broken_other/total_other

                        total_web_page_min = total_web_page
                        total_js_min = total_js
                        total_css_min = total_css
                        total_image_min = total_image
                        total_other_min = total_other
                        min_broken_res_count = total_broken_rate
                    print("total:", res_count, " broken res:", broken_res_count, " stamp: ",
                          profile.date_stamp, " pass? ", passed, " rate:", total_broken_rate)
        return ArchiveDetail(root_domain, archive_link=ArchiveOrg.get_archive_link(archive), total_res=res_count, good_res_rate=min_broken_res_count,
                             total_web_page=total_web_page_min, good_webpage_rate=good_rate_web_page,
                             total_css=total_css_min, good_css_rate=good_rate_css,
                             total_js=total_js_min,  good_js_rate=good_rate_js,
                             total_image=total_image_min, good_image_rate=good_rate_image,
                             total_other=total_other_min, good_other_rate=good_rate_other)