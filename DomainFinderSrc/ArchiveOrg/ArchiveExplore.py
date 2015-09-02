from DomainFinderSrc.Scrapers.LinkChecker import LinkChecker
import re
from urllib.parse import urlsplit
from multiprocessing import pool
import multiprocessing
import threading
import bs4
import requests
from DomainFinderSrc.Scrapers.SiteFileManager import SiteFileManager
from DomainFinderSrc.Utilities import FilePath, FileIO
import functools


#archive_link_pattern = re.compile("(\/web\/.+)(http.+\/.+\.[a-z]{0,5})")
archive_link_pattern = re.compile(u'(\/web[^\'"\(\)]*)(http[^\'"\(\)]*)')
css_link_pattern = re.compile(u'(\/web\/.+)(http.+\/.+\.[a-z]{2,4})')
link_pattern = re.compile(u'["\'\(]\s*(\/web[^\'"\(\)]*)(http[^\'"\(\)]*)\s*["\'\)]')


class PageAttrs:
    def __init__(self, path: str, level: int, signature, is_broken: bool, is_duplicate: bool, page_type: str):
        self.path = path
        self.level = level
        self.signature = signature
        self.is_broken = is_broken
        self.is_duplicate = is_duplicate
        self.page_type = page_type


class LinkAttrs(object):
    def __init__(self, link: str, path: str, ref_link: str, source: str, page_type: str, level: int, is_anchor=False):
        """
        attribute of a link, e.g: "http://web.archive.org/web/20140711025724/http://susodigital.com/"
        :param link: full link, e.g: http://web.archive.org/web/20140711025724/http://susodigital.com/
        :param path: path to site dir: e.g: "/"
        :param ref_link: link text with in original page
        :param source: the local source file that contains the ref_link
        :param page_type: type of a link, LinkUtility type e.g: EXT_CSS
        :param level: level at which the link was found
        :param is_anchor:determine if the link is found in an anchor or not
        :return:
        """
        self.link = link
        self.path = path
        self.ref_link = ref_link
        self.source = source
        self.page_type = page_type
        self.level = level
        self.is_anchor = is_anchor

    def __str__(self):
        # return "link: "+self.link+" file_path: "+self.path+" type: "+self.page_type+" lvl: "+str(self.level)
        return str(self.__dict__)

class LinkUtility:
    EXT_CSS = 'css'
    EXT_FONT = 'font'
    EXT_JS = 'js'
    EXT_WEBPAGE = 'html'
    EXT_IMAGE = 'image'
    EXT_OTHER = 'other'

    DEFAULT_HOME_PAGE_PATH = "/index.html"

    @staticmethod
    def get_link_class(link: str) -> (str, str):
        ext = LinkChecker.get_link_extension(link).lower()
        if len(ext) == 0 or ext in LinkChecker.common_html_page_ex:
            return LinkUtility.EXT_WEBPAGE, ext
        elif ext in LinkChecker.common_img_ex:
            return LinkUtility.EXT_IMAGE, ext
        elif ext in LinkChecker.common_font_ex:
            return LinkUtility.EXT_FONT, ext
        elif ext.endswith("css"):
            return LinkUtility.EXT_CSS, ext
        elif ext.endswith("js"):
            return LinkUtility.EXT_JS, ext
        else:
            return LinkUtility.EXT_OTHER, ext

    @staticmethod
    def make_valid_web_res_path(path: str, args="") -> (str, str):
        """
        change a web resource path so that it can save a file in file system and also can be ref in a webpage
        :param path: a web resource path, such as /allpage/nextpage#ok
        :return:tuple(path in file system, ref path in webpage) e.g: (/allpage/nextpage.html, /allpage/nextpage.html#ok)
        """
        is_use_js_seperator = True if path.find("\\/") > 0 else False
        if is_use_js_seperator:
            path = path.replace("\\/", "/")
        file_path = path
        if len(args) > 0:
            ref_path = path #+ "?" + args
        else:
            ref_path = path
        if len(path) == 0 or path == "/":
            file_path = LinkUtility.DEFAULT_HOME_PAGE_PATH
            ref_path = "/"
        elif path.startswith('/#'):
            file_path = path.replace('/#', LinkUtility.DEFAULT_HOME_PAGE_PATH)
            # ref_path = path.replace('/#', LinkUtility.DEFAULT_HOME_PAGE_PATH+"#")
        elif path.endswith('/'):
            file_path = path.rstrip('/') + LinkUtility.DEFAULT_HOME_PAGE_PATH
            # ref_path = file_path
        if is_use_js_seperator:
            ref_path = ref_path.replace("/", "\\/")  # replace back
        return file_path, ref_path

    @staticmethod
    def get_link_detail(link: str) -> (str, str, str, str, str):
        """
        link info about an archive link matched with link_pattern
        :param link:
        :return:
        """
        match = re.search(archive_link_pattern, link)
        if match is not None:
            groups = match.groups()
            if isinstance(groups, tuple) and len(groups) == 2:
                archive_profile, inner_link = groups
                parameters = urlsplit(inner_link)
                domain = parameters[1]
                path = parameters[2]
                args = parameters[3]
                link_class, ext = LinkUtility.get_link_class(path)
                if len(ext) == 0 and not path.endswith('/') and link_class == LinkUtility.EXT_WEBPAGE:
                    path += "/"
                return inner_link, domain, path, link_class, args
            else:
                return "", "", "", "", ""
        else:
            return "", "", "", "", ""

    @staticmethod
    def _slice_middle_text(text: str, begin_pattern: str, end_pattern: str):
        len_original = len(text)
        if len_original == 0:
            return ""
        insert_begin_index = text.index(begin_pattern)
        insert_fin_index = text.index(end_pattern) + len(end_pattern)
        if insert_begin_index > 0 and insert_fin_index > 0:
            return text[:insert_begin_index] + text[insert_fin_index:]
        else:
            return text

    @staticmethod
    def remove_archive_org_footprint(archive: str) -> bs4.BeautifulSoup:
        after_tool_bar_text = LinkUtility._slice_middle_text(archive, '<!-- BEGIN WAYBACK TOOLBAR INSERT -->',
                                                             '<!-- END WAYBACK TOOLBAR INSERT -->')
        html_fin_tag = "</html>"
        finish_index = after_tool_bar_text.index(html_fin_tag)
        archive = after_tool_bar_text[:finish_index + len(html_fin_tag)]
        soup = bs4.BeautifulSoup(archive)
        app_bar = soup.find("#wm-ipp")
        if isinstance(app_bar, bs4.Tag):
            app_bar.decompose()
        no_use_scripts = soup.find_all("script")
        for item in no_use_scripts:
            if isinstance(item, bs4.Tag):
                if "src" in item.attrs and item["src"] == "/static/js/analytics.js":
                    item.decompose()
                elif item.text.startswith("archive_analytics.values"):
                    item.decompose()
        no_use_links = soup.find_all("link")
        for link_item in no_use_links:
            if isinstance(link_item, bs4.Tag):
                if "href" in link_item.attrs and link_item["href"] == "/static/css/banner-styles.css":
                    link_item.decompose()

        return soup
        #archive = LinkUtility._slice_middle_text(after_tool_bar_text, "FILE ARCHIVED ON", "SECTION 108(a)(3)).")


class ArchiveExplorer:
    ARCHIVE_DOMAIN = "http://web.archive.org"

    def __init__(self, original_domain: str, link: str, external_stop_event: multiprocessing.Event, max_thread: int=1,
                 download_content=True, download_base_dir=None, max_level=2, max_page=200):
        self._original_domain = original_domain
        self._archive_link = link
        self._external_stop_event = external_stop_event
        self._internal_pages = []  # an array of PageAttrs  for page comparison
        self._external_ref_page = []  # an array of PageAttrs for page comparison
        self._internal_list = []  # an array of LinkAttrs for checking download list
        self._broken_res_list = []
        inner_link, domain, path, ext, args = LinkUtility.get_link_detail(link)
        file_path, ref_path = LinkUtility.make_valid_web_res_path(path, args)
        self._internal_list.append(LinkAttrs(link=link, path=file_path, ref_link=ref_path, source=file_path,
                                             page_type=LinkUtility.EXT_WEBPAGE, level=0))
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
        self._pool = None
        self._sync_lock = threading.RLock()
        self._broken_link_count = 0
        self._broken_image_count = 0
        self._broken_css_count = 0
        self._broken_js_count = 0
        self._total_res_done = 0
        self._total_page_done = 0
        self._timeout = 10
        self._allow_retries = 3
        self._allow_redirect = 3

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
            print("cap:", link)
            match2 = current_match.group(2)
            current_link = current_match.group(1) + match2
            begin_index = str(link).index("/")
            begin_mark = str(link[:begin_index]).strip()
            end_index = begin_index + len(current_link)
            if end_index >= len(link):
                end_mark = ""
            else:
                end_mark = str(link[end_index:]).strip()
            inner_link, domain, path, ext, args = LinkUtility.get_link_detail(current_link)
            if len(inner_link) > 0:
                if root_domain not in domain and ext == LinkUtility.EXT_WEBPAGE:
                    returned = begin_mark + match2 + end_mark
                else:  # capture other resources except external webpage
                    file_path, ref_path = LinkUtility.make_valid_web_res_path(path)
                    captured.append(LinkAttrs(ArchiveExplorer.ARCHIVE_DOMAIN+current_link, file_path, ref_path, file_path, ext, level+1))
                    returned = begin_mark + ref_path + end_mark
            else:
                returned = begin_mark + current_link + end_mark
        except Exception as ex:
            print("ex in mapping:", ex)
        finally:
            if isinstance(returned, str):
                print("sub:", returned)
                return returned
            else:
                return ""

    def _parse_text_res(self, page: LinkAttrs) -> str:
        page.link = page.link.replace("\\/", "/")  # in case of javascript
        response = LinkChecker.get_common_web_resource(page.link, timeout=self._timeout,
                                                       redirect=self._allow_redirect, retries=self._allow_retries)
        result = ""
        groups = []
        parse_str_sp = functools.partial(ArchiveExplorer._map_res_str, groups, self._original_domain, page)
        if page.page_type == LinkUtility.EXT_WEBPAGE:
            text = str(LinkUtility.remove_archive_org_footprint(response.text))
        else:
            text = response.text
        result = re.sub(link_pattern, parse_str_sp, text)
        for item in groups:
            if isinstance(item, LinkAttrs):
                if not ArchiveExplorer._is_in_list(item.path, self._internal_list):
                    if (page.page_type == LinkUtility.EXT_WEBPAGE and self._current_level < self._max_level) or self._current_level < self._max_level+1:
                        # allow html page one level above other resources
                        with self._sync_lock:
                            # print("appending:", item)
                            if item.page_type == LinkUtility.EXT_OTHER:
                                print("find unknown type in text res file:", page.link, "currentlink:", item.link)
                            self._internal_list.append(item)
        return result

    def _parse_webpage_v0(self, page: LinkAttrs) -> str:
        page_source = LinkChecker.get_page_source(page.link, timeout=self._timeout, redirect=self._allow_redirect, retries=self._allow_retries)
        bs4_tree = LinkUtility.remove_archive_org_footprint(page_source.text)
        for child in bs4_tree.find_all():
            current_link = None
            is_anchor = False
            if isinstance(child, bs4.Tag):
                if "href" in child.attrs:
                    current_link = child["href"]
                    if child.name == "a":
                        is_anchor = True
                elif "src" in child.attrs:
                    current_link = child["src"]
            if isinstance(current_link, str):
                inner_link, domain, path, ext, args = LinkUtility.get_link_detail(current_link)
                if ext == LinkUtility.EXT_OTHER: # TODO: change this
                    print("find unknown type in webpage:", page.link, "currentlink:", current_link)
                if len(inner_link) > 0:
                    if current_link.startswith('/web/'):
                        current_link = ArchiveExplorer.ARCHIVE_DOMAIN+current_link
                    file_path, ref_path = LinkUtility.make_valid_web_res_path(path, args)  # make webpage as file path
                    if self._current_level < self._max_level and not ArchiveExplorer._is_in_list(file_path, self._internal_list):
                        if self._original_domain in domain:  # internal res
                                with self._sync_lock:  # add to the download list
                                    self._internal_list.append(LinkAttrs(current_link,
                                                                         file_path, ref_path, page.path,
                                                                         ext, page.level+1, is_anchor))

                        else:
                            if ext == LinkUtility.EXT_WEBPAGE:  # keep external page reference without download it
                                ref_path = inner_link
                            else:  # download all other resources
                                with self._sync_lock:  # add to the download list
                                    self._internal_list.append(LinkAttrs(current_link, file_path,
                                                                         ref_path, page.path, ext, page.level+1))
                        # print(inner_link)
                        # print("level ", self._current_level, " -> ", file_path)

                    if isinstance(child, bs4.Tag):
                        if "href" in child.attrs:
                            print("change ref_path:", ref_path)
                            child["href"] = ref_path
                        elif "src" in child.attrs:
                            print("change ref_path:", ref_path)
                            child["src"] = ref_path
        return str(bs4_tree)

    def scrape_web_res(self, page: LinkAttrs):
        print("look:", page.link)
        try:
            if page.page_type in [LinkUtility.EXT_WEBPAGE, LinkUtility.EXT_CSS, LinkUtility.EXT_JS]:  # parse a webpage
                save_text = self._parse_text_res(page)
                self._file_manager.write_to_file(page.path, save_text)
            # elif page.page_type != LinkUtility.EXT_OTHER:  # TODO: download normal resources
            #     response = LinkChecker.get_common_web_resource(page.link)
            #     if page.page_type == LinkUtility.EXT_IMAGE or page.page_type == LinkUtility.EXT_FONT:
            #         self._downloader.write_to_file(page.path, response.content, mode="b")
            #     else:
            #         self._downloader.write_to_file(page.path, response.text, mode="t")
            else:
                # response = LinkChecker.get_common_web_resource(page.link)
                # self._downloader.write_to_file(page.path, response.content, mode="b")
                self._file_manager.download_file(sub_path=page.path, url=page.link, timeout=self._timeout)
        except Exception as ex:
            print("exception:", ex)
            print("broken res:", page)
            with self._sync_lock:
                if page.page_type == LinkUtility.EXT_WEBPAGE:
                    self._broken_link_count += 1
                elif page.page_type == LinkUtility.EXT_CSS:
                    self._broken_css_count += 1
                elif page.page_type == LinkUtility.EXT_IMAGE:
                    self._broken_image_count += 1
                elif page.page_type == LinkUtility.EXT_JS:
                    self._broken_js_count += 1
                self._broken_res_list.append(page)
        finally:
            with self._sync_lock:
                self._total_res_done += 1
                if page.page_type == LinkUtility.EXT_WEBPAGE:
                    self._total_page_done += 1

    def _get_next_level(self, level: int):
        return [x for x in self._internal_list if x.level == level]

    def begin_scrape(self, level=0):
        if self._pool is None:
            self._pool = pool.ThreadPool(processes=self._max_thread)
        res = self._get_next_level(level)
        if len(res) > 0:
            result = self._pool.map(func=self.scrape_web_res, iterable=res)
            self._current_level += 1
            self.begin_scrape(self._current_level)
        else:
            return

    def _fix_broken_links(self):
        source_pages = set([x.source for x in self._broken_res_list])
        for source in source_pages:
            replace_links = set([y.ref_link for y in self._broken_res_list if y.source == source and y.is_anchor and
                                self._original_domain not in y.ref_link and not self._file_manager.exist_in_path(y.path)])
            source_file = self._file_manager.read_from_file(source)
            if isinstance(source_file, str):
                for link in replace_links:
                    print("fix file:", source, " link: ", link, " with:", "/")
                    source_file.replace(link, "/")
                self._file_manager.write_to_file(source, source_file)

    def run(self):
        self.begin_scrape(0)
        print("total_res: ", self._total_res_done, " page done:", self._total_page_done, " broken page:", self._broken_link_count,
              " broken image: ", self._broken_image_count, " broken css: ", self._broken_css_count, " broken js: ", self._broken_js_count)
        self._fix_broken_links()