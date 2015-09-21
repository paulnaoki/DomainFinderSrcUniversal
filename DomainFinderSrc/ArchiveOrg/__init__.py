import re
from urllib.parse import urlsplit
import bs4
from DomainFinderSrc.Scrapers.LinkChecker import LinkChecker
from DomainFinderSrc.Utilities.Serializable import Serializable
from urllib import parse

#archive_link_pattern = re.compile("(\/web\/.+)(http.+\/.+\.[a-z]{0,5})")
archive_link_pattern = re.compile(u'(\/web[^\'"\(\)]*)\/(http[^\'"\(\)]*)')


class ArchiveStruct(Serializable):
    def __init__(self, link: str, date_stamp: str, size: int):
        self.link = link
        self.date_stamp = date_stamp
        self.size = size

    def __str__(self):
        return "link: " + self.link + " time_stamp: " + self.date_stamp + " size: " + str(self.size)


class ArchiveDetail:
    def __init__(self, domain: str, archive_link: str, total_res: int, good_res_rate: float,
                 total_web_page: int, good_webpage_rate: float,
                 total_css: int, good_css_rate: float,
                 total_js: int, good_js_rate: float,
                 total_image: int, good_image_rate: float,
                 total_other: int, good_other_rate: float):
        self.domain = domain
        self.archive_link = archive_link
        self.total_res = total_res
        self.good_res_rate = good_res_rate
        self.total_web_page = total_web_page
        self.good_webpage_rate = good_webpage_rate
        self.total_css = total_css
        self.good_css_rate = good_css_rate
        self.total_js = total_js
        self.good_js_rate = good_js_rate
        self.total_image = total_image
        self.good_image_rate = good_image_rate
        self.total_other = total_other
        self.good_other_rate = good_other_rate

    @staticmethod
    def get_title():
        return "DOMAIN", "ARCHIVE_LINK", "TOTAL_RES", "TOTAL GOOD RES %", "WEB PAGE", "GOOD WEB PAGE %", "CSS", "GOOD CSS %", \
               "TOTAL JS", "GOOD JS RATE %", "IMAGE", "GOOD IMAGE RATE", "OTHERS", "GOOD OTHERS RATE"

    def to_tuple(self):
        return self.domain, self.archive_link, self.total_res, self.good_res_rate, self.total_web_page, self.good_webpage_rate, \
            self.total_css, self.good_css_rate, self.total_js, self.good_js_rate, self.total_image, self.good_image_rate,\
            self.total_other, self.good_other_rate


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
    def make_valid_web_res_path(path: str, fragment="") -> (str, str):
        """
        for internal resources only.
        change a web resource path so that it can save a file in file system and also can be ref in a webpage
        :param path: a web resource path, such as /allpage/nextpage#ok
        :return:tuple(path in file system, ref path in webpage) e.g: (/allpage/nextpage.html, /allpage/nextpage.html#ok)
        """
        # TODO: add the case of url-encoded path, also if the path is too long for file system
        is_use_js_seperator = True if "\\/" in path else False
        if is_use_js_seperator:
            path = path.replace("\\/", "/")
        file_path = path
        ref_path = path
        if len(path) == 0 or path == "/":
            file_path = LinkUtility.DEFAULT_HOME_PAGE_PATH
            ref_path = "/"
        elif path.startswith('/#'):
            file_path = LinkUtility.DEFAULT_HOME_PAGE_PATH
            # file_path = path.replace('/#', LinkUtility.DEFAULT_HOME_PAGE_PATH)
            # ref_path = path.replace('/#', LinkUtility.DEFAULT_HOME_PAGE_PATH+"#")
        elif path.endswith('/'):
            file_path = path.rstrip('/') + LinkUtility.DEFAULT_HOME_PAGE_PATH
        if is_use_js_seperator:
            ref_path = ref_path.replace("/", "\\/")  # replace back

        if len(fragment) > 0:
            ref_path += "#" + fragment

        file_path = parse.unquote(file_path).replace("//", "/")
        ref_path = ref_path.replace("//", "/")
        return file_path, ref_path

    @staticmethod
    def get_link_detail(link: str) -> (str, str, str, str, str):
        """
        link info about an archive link matched with link_pattern
        :param link:
        :return:
        """
        # link = parse.unquote(link)
        match = re.search(archive_link_pattern, link)
        if match is not None:
            groups = match.groups()
            if isinstance(groups, tuple) and len(groups) == 2:
                archive_profile, inner_link = groups
                parameters = urlsplit(inner_link)
                domain = parameters[1]
                path = parameters[2]
                fragment = parameters[4]
                link_class, ext = LinkUtility.get_link_class(path)
                if len(ext) == 0 and not path.endswith('/') and link_class == LinkUtility.EXT_WEBPAGE:
                    path += "/"
                return inner_link, domain, path, link_class, ext, fragment

            else:
                return "", "", "", "", "", ""
        else:
            return "", "", "", "", "", ""

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


class PageAttrs:
    def __init__(self, path: str, level: int, signature, is_broken: bool, is_duplicate: bool, page_type: str):
        self.path = path
        self.level = level
        self.signature = signature
        self.is_broken = is_broken
        self.is_duplicate = is_duplicate
        self.page_type = page_type


class LinkAttrs(object):
    def __init__(self, link: str, path: str, ref_link: str, shadow_ref_link: str, source: str, res_type: str, level: int, is_anchor=False,
                 is_internal=True):
        """
        attribute of a link, e.g: "http://web.archive.org/web/20140711025724/http://susodigital.com/"
        :param link: full link, e.g: http://web.archive.org/web/20140711025724/http://susodigital.com/
        :param path: path to site dir: e.g: "/"
        :param ref_link: link text within original page, could be modified due to long length or unsuitable webpage extension
        :param shadow_ref_link: un-modified link text within original page
        :param source: the local source file that contains the ref_link
        :param res_type: type of a link, LinkUtility type e.g: EXT_CSS
        :param level: level at which the link was found
        :param is_anchor:determine if the link is found in an anchor or not
        :return:
        """
        self.link = link
        self.path = path
        self.ref_link = ref_link
        self.shadow_ref_link = shadow_ref_link
        self.source = source
        self.res_type = res_type
        self.level = level
        self.is_anchor = is_anchor
        self.is_internal = is_internal

    def __str__(self):
        # return "link: "+self.link+" file_path: "+self.path+" type: "+self.res_type+" lvl: "+str(self.level)
        return str(self.__dict__)

    @staticmethod
    def get_titles():
        return "LINK", "PATH", "REF_LINK", "SHADOW_REF_LINK", "SOURCE", "TYPE", "LEVEL", "IS ANCHOR", "IS INTERNAL", "ERROR"

    def to_tuple(self, error=""):
        return self.link, self.path, self.ref_link, self.shadow_ref_link, self.source, self.res_type, self.level, \
               self.is_anchor, self.is_internal, error