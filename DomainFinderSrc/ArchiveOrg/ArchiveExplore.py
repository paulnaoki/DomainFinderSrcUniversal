import re
from multiprocessing import pool
import multiprocessing
import threading
import functools
import bs4
from DomainFinderSrc.ArchiveOrg import LinkUtility, LinkAttrs
from DomainFinderSrc.Scrapers.LinkChecker import LinkChecker, ResponseCode
from DomainFinderSrc.Scrapers.SiteFileManager import SiteFileManager
from DomainFinderSrc.Utilities import FilePath
from DomainFinderSrc.ArchiveOrg import ArchiveDetail
from urllib import parse


css_link_pattern = re.compile(u'(\/web\/.+)(http.+\/.+\.[a-z]{2,4})')
link_pattern = re.compile(u'["\'\(]\s*(\/web[^\'"\(\)]*)(http[^\'"\(\)]*)\s*["\'\)]')


class ArchiveExplorer:
    ARCHIVE_DOMAIN = "http://web.archive.org"
    MAX_PATH_LEN = 100

    def __init__(self, original_domain: str, link: str, external_stop_event: multiprocessing.Event, max_thread: int=1,
                 download_content=True, download_base_dir=None, max_level=2, max_page=200):
        self._original_domain = original_domain
        self._archive_link = link
        self._external_stop_event = external_stop_event
        self._internal_pages = []  # an array of PageAttrs  for page comparison
        self._external_ref_page = []  # an array of PageAttrs for page comparison
        self._internal_list = []  # an array of LinkAttrs for checking download list
        self._broken_res_list = []
        inner_link, domain, path, link_class, ext, fragment = LinkUtility.get_link_detail(link)
        file_path, ref_path = LinkUtility.make_valid_web_res_path(path, fragment)
        self._internal_list.append(LinkAttrs(link=link, path=file_path, ref_link=ref_path, shadow_ref_link=ref_path,
                                             source=file_path,
                                             res_type=LinkUtility.EXT_WEBPAGE, level=0))
        self._max_thread = max_thread
        self._max_level = max_level
        self._current_level = 0
        self._max_page = max_page
        if max_thread < 1:
            self._max_thread = 1
        self._download_content = download_content
        if self._download_content and download_base_dir is None:
            raise ValueError("ArchiveExplorer.__init__: download_base_dir cannot be None.")
        self._file_manager = SiteFileManager(base_dir_path=FilePath.get_default_archive_dir(), file_name=original_domain)
        self._file_manager.write_to_error_log(LinkAttrs.get_titles())
        self._max_redirect = 5
        self._max_retries = 2
        self._pool = None
        self._sync_lock = threading.RLock()

        self._broken_webpage_count = 0
        self._broken_image_count = 0
        self._broken_css_count = 0
        self._broken_js_count = 0
        self._broken_others_count = 0

        self._total_webpage_count = 0
        self._total_image_count = 0
        self._total_css_count = 0
        self._total_js_count = 0
        self._total_others_count = 0

        self._total_res_done = 0

        self._timeout = 10

    def get_archive_detail(self) -> ArchiveDetail:
        good_webpage_percent = 0 if self._total_webpage_count == 0 else 1 - self._broken_webpage_count/self._total_webpage_count
        good_image_percent = 0 if self._total_image_count == 0 else 1 - self._broken_image_count/self._total_image_count
        good_js_percent = 0 if self._total_js_count == 0 else 1 - self._broken_js_count/self._total_js_count
        good_css_percent = 0 if self._total_css_count == 0 else 1 - self._broken_css_count/self._total_css_count
        good_others_percent = 0 if self._total_others_count == 0 else 1 - self._broken_others_count/self._total_others_count
        all_broken = self._broken_js_count + self._broken_css_count + self._broken_image_count + self._broken_others_count + self._broken_webpage_count
        good_overall_percent = 0 if self._total_res_done == 0 else 1 - all_broken/self._total_res_done
        return ArchiveDetail(self._original_domain, self._archive_link, self._total_res_done,
                             good_res_rate=good_overall_percent, total_web_page=self._total_webpage_count,
                             good_webpage_rate=good_webpage_percent, total_css=self._total_css_count, good_css_rate=good_css_percent,
                             total_js=self._total_js_count, good_js_rate=good_js_percent, total_image=self._total_image_count,
                             good_image_rate=good_image_percent, total_other=self._total_others_count, good_other_rate=good_others_percent)

    @staticmethod
    def is_downloadable_content(link_data: LinkAttrs, max_level: int):
        if link_data.res_type == LinkUtility.EXT_WEBPAGE and link_data.is_internal and link_data.level <= max_level:
            return True
        elif not link_data.res_type == LinkUtility.EXT_WEBPAGE:
            return True
        else:
            return False

    @staticmethod
    def _is_in_list(source: str, target_list: []) -> bool:
        """
        determine if a path is in list already.
        :param source: source path
        :param target_list: a list of LinkAttrs, could be js, css, webpage, other resource path
        :return:
        """
        is_in = False
        for item in target_list:
            if isinstance(item, LinkAttrs):
                if source == item.path:
                    is_in = True
                    break
        return is_in

    @staticmethod
    def _map_res_str(captured: [], root_domain: str, page: LinkAttrs, current_match) -> str:
        returned = None
        level = page.level
        try:
            link = current_match.group(0)
            # print("cap:", link)
            match2 = current_match.group(2)
            current_link = current_match.group(1) + match2
            begin_index = str(link).index("/")
            begin_mark = str(link[:begin_index]).strip()
            end_index = begin_index + len(current_link)
            if end_index >= len(link):
                end_mark = ""
            else:
                end_mark = str(link[end_index:]).strip()
            # if "%3" in current_link:  # transform encoded url
            inner_link, domain, path, link_class, ext, fragment = LinkUtility.get_link_detail(current_link)
            if len(inner_link) > 0:
                if root_domain in domain or link_class != LinkUtility.EXT_WEBPAGE:  # data will be saved in file system
                    if root_domain in domain:
                        is_internal = True
                    else:
                        is_internal = False
                    path_decoded = parse.unquote(path)
                    if len(path_decoded) > ArchiveExplorer.MAX_PATH_LEN:
                        short_path, ext = LinkChecker.get_shorter_url_path(path)
                        short_path += ext
                    else:
                        short_path = path
                    if link_class == LinkUtility.EXT_WEBPAGE:
                        if len(ext) > 0 and not ext == ".html":
                            valid_short_path = short_path.replace(ext, ".html")
                        else:
                            valid_short_path = short_path
                    else:
                        valid_short_path = short_path
                    file_path, ref_path = LinkUtility.make_valid_web_res_path(path, fragment)
                    short_file_path, short_ref_path = LinkUtility.make_valid_web_res_path(valid_short_path, fragment)
                    current_link = current_link.replace("\\/", "/")
                    captured.append(LinkAttrs(ArchiveExplorer.ARCHIVE_DOMAIN+current_link, short_file_path,
                                              short_ref_path, ref_path,
                                              page.path, link_class, level+1, is_internal=is_internal))
                    returned = begin_mark + short_ref_path + end_mark
                else: #root_domain not in domain and ext == LinkUtility.EXT_WEBPAGE:
                    returned = begin_mark + parse.unquote(match2) + end_mark
                # else:  # capture other resources except external webpage
                #     file_path, ref_path = LinkUtility.make_valid_web_res_path(path)
                #     captured.append(LinkAttrs(ArchiveExplorer.ARCHIVE_DOMAIN+current_link, file_path, ref_path, file_path, ext, level+1))
                #     returned = begin_mark + ref_path + end_mark
            else:
                returned = begin_mark + parse.unquote(current_link) + end_mark
        except Exception as ex:
            print("ex in mapping:", ex)
        finally:
            if isinstance(returned, str):
                # print("sub:", returned)
                return returned
            else:
                return ""

    def _parse_text_res(self, page: LinkAttrs) -> str:
        page.link = page.link.replace("\\/", "/")  # in case of javascript
        response = LinkChecker.get_common_web_resource(page.link, timeout=self._timeout,
                                                       redirect=self._max_redirect, retries=self._max_retries)
        result = ""
        groups = []
        parse_str_sp = functools.partial(ArchiveExplorer._map_res_str, groups, self._original_domain, page)
        if page.res_type == LinkUtility.EXT_WEBPAGE:
            text = str(LinkUtility.remove_archive_org_footprint(response.text))
        else:
            text = response.text
        result = re.sub(link_pattern, parse_str_sp, text)
        for item in groups:
            if isinstance(item, LinkAttrs):
                if not ArchiveExplorer._is_in_list(item.path, self._internal_list) and\
                        ArchiveExplorer.is_downloadable_content(item, self._max_level):
                    with self._sync_lock:
                        # print("appending:", item)
                        # print("adding to list:", item.link, "level: ", item.level)
                        if not item.shadow_ref_link == item.ref_link:
                            self._file_manager.write_to_redirect(item.shadow_ref_link, item.ref_link)
                        self._internal_list.append(item)

        return result

    def scrape_web_res(self, page: LinkAttrs):
        print("look:", page.link, "level: ", page.level)
        try:
            if len(page.path) > ArchiveExplorer.MAX_PATH_LEN:  # max file path in any file system
                raise OSError("file path is too long:" + page.path)
            response_code, content_type = LinkChecker.get_response(page.link)
            if response_code not in [ResponseCode.LinkOK, ResponseCode.LinkFound, ResponseCode.LinkRedirect]:
                raise ConnectionError("res is not available: " + page.link)
            if page.res_type in [LinkUtility.EXT_WEBPAGE, LinkUtility.EXT_CSS, LinkUtility.EXT_JS]:  # parse a webpage
                save_text = self._parse_text_res(page)
                self._file_manager.write_to_file(page.path, save_text)
            # elif page.res_type != LinkUtility.EXT_OTHER:  # TODO: download normal resources
            #     response = LinkChecker.get_common_web_resource(page.link)
            #     if page.res_type == LinkUtility.EXT_IMAGE or page.res_type == LinkUtility.EXT_FONT:
            #         self._downloader.write_to_file(page.path, response.content, mode="b")
            #     else:
            #         self._downloader.write_to_file(page.path, response.text, mode="t")
            else:
                # response = LinkChecker.get_common_web_resource(page.link)
                # self._downloader.write_to_file(page.path, response.content, mode="b")
                self._file_manager.download_file(sub_path=page.path, url=page.link, timeout=self._timeout,
                                                 redirect=self._max_redirect, retries=self._max_retries)
        except Exception as ex:
            print("exception:", ex)
            print("broken res:", page)
            with self._sync_lock:
                self._file_manager.write_to_error_log(page.to_tuple(str(ex)))
                if page.res_type == LinkUtility.EXT_WEBPAGE:
                    self._broken_webpage_count += 1
                elif page.res_type == LinkUtility.EXT_CSS:
                    self._broken_css_count += 1
                elif page.res_type == LinkUtility.EXT_IMAGE:
                    self._broken_image_count += 1
                elif page.res_type == LinkUtility.EXT_JS:
                    self._broken_js_count += 1
                else:
                    self._broken_others_count += 1

                self._broken_res_list.append(page)
        finally:
            with self._sync_lock:
                self._total_res_done += 1
                if page.res_type == LinkUtility.EXT_WEBPAGE:
                    self._total_webpage_count += 1
                elif page.res_type == LinkUtility.EXT_CSS:
                    self._total_css_count += 1
                elif page.res_type == LinkUtility.EXT_IMAGE:
                    self._total_image_count += 1
                elif page.res_type == LinkUtility.EXT_JS:
                    self._total_js_count += 1
                else:
                    self._total_others_count += 1

    def _get_next_level(self, level: int):
        return [x for x in self._internal_list if x.level == level]

    def begin_scrape(self, level=0):
        res = self._get_next_level(level)
        print("checking level:", level, " res count:", len(res))
        if len(res) > 0:
            self._pool = pool.ThreadPool(processes=self._max_thread)
            result = self._pool.map(func=self.scrape_web_res, iterable=res)
            self._current_level += 1
            self._pool.terminate()
            self.begin_scrape(self._current_level)
        else:
            return

    def _fix_broken_links(self):
        broken_res_path = [y.path for y in self._broken_res_list]
        replace_res_type = [LinkUtility.EXT_WEBPAGE, LinkUtility.EXT_JS, LinkUtility.EXT_CSS]
        source_page = set([x.path for x in self._internal_list if x.path not in broken_res_path
                           and x.res_type in replace_res_type])
        for source in source_page:
            source_file = self._file_manager.read_from_file(source)
            if isinstance(source_file, str):
                for res in self._broken_res_list:
                    print("fix file:", source, " link: ", res.ref_link, " with:", "/")
                    source_file = source_file.replace(res.ref_link, "/")
                self._file_manager.write_to_file(source, source_file)

    def _fix_broken_links_v0(self):
        source_pages = set([x.path for x in self._broken_res_list])
        for source in source_pages:
            replace_links = set([y.ref_link for y in self._broken_res_list if y.source == source and y.is_anchor and
                                self._original_domain not in y.ref_link and not self._file_manager.exist_in_path(y.path)])
            source_file = self._file_manager.read_from_file(source)
            if isinstance(source_file, str):
                for link in replace_links:
                    print("fix file:", source, " link: ", link, " with:", "/")
                    source_file = source_file.replace(link, "/")
                self._file_manager.write_to_file(source, source_file)

    def run(self):
        self.begin_scrape(0)
        self._fix_broken_links()
        print("total_res: ", self._total_res_done, " page done:", self._total_webpage_count, " broken page:", self._broken_webpage_count,
              " broken image: ", self._broken_image_count, " broken css: ", self._broken_css_count, " broken js: ", self._broken_js_count)