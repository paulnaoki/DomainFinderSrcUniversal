from unittest import TestCase
from DomainFinderSrc.ArchiveOrg.ProfileExtract import ArchiveOrg, ArchiveStruct
from DomainFinderSrc.ArchiveOrg.ArchiveExplore import *
from DomainFinderSrc.Scrapers.LinkChecker import LinkChecker
import bs4
import multiprocessing
import re
from DomainFinderSrc.Utilities.FileIO import FileHandler
import functools


def test_response(link: str) -> bool:
    status_code, content_type = LinkChecker.get_response(link)
    if status_code != 200:
        print(link, "status bad:", status_code, " content: ", content_type)
        return False
    else:
        print(link, "status good:", status_code, " content: ", content_type)
        return True


def parse_str(captured: [], level: int, current_match) -> str:
    root_domain = "bbc.co.uk"
    returned = None
    try:
        link = current_match.group(0)
        print("capture:", link)
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
        print(ex)
    finally:
        if isinstance(returned, str):
            print("returning:", returned)
            return returned
        else:
            return ""


class ArchiveOrgTest(TestCase):

    def testSlice(self):
        array = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        changed = array[:-10:-1]
        print(changed)

    def testRe(self):
        css_text = FileHandler.read_all_from_file("/Users/superCat/Desktop/PycharmProjectPortable/test/example.css")
        test_s = "if('undefined' === typeof wwhomepage) var wwhomepage = {}; wwhomepage.customPromoHeaders = {\" /web/20130415001342/http://www.bbc.co.uk\/news\/magazine-22094279\":"
        match = re.search(link_pattern, css_text)
        groups = match.group()
        if match is not None:
            for i in match.groups(0):
                print(i)

    def testCssParse(self):
        css_text = FileHandler.read_all_from_file("/Users/superCat/Desktop/PycharmProjectPortable/test/example.css")

        section = css_text.split("}")
        groups = []
        parse_str_sp = functools.partial(parse_str, groups, 1)
        result = ""
        for sec in section:
            sec += "}"
            temp = re.sub(css_link_pattern, parse_str_sp, sec)
            result += temp
        for item in groups:
            print(item)

        print(result)

    def testCss2Parse(self):
        css_text = FileHandler.read_all_from_file("/Users/superCat/Desktop/PycharmProjectPortable/test/example.css")
        groups = []
        parse_str_sp = functools.partial(parse_str, groups, 1)
        temp = re.sub(link_pattern, parse_str_sp, css_text)
        # for item in groups:
        #     print(item)
        print("captured total: ", len(groups))
        for item in groups:
            if isinstance(item, LinkAttrs):
                print("res:", item.path,  "link:", item.link)

        #print(temp)

    def testHtmlParse(self):
        html_text = FileHandler.read_all_from_file("/Users/superCat/Desktop/PycharmProjectPortable/test/example.html")
        groups = []
        parse_str_sp = functools.partial(parse_str, groups, 1)
        temp = re.sub(link_pattern, parse_str_sp, html_text)
        # for item in groups:
        #     print(item)
        print("captured total: ", len(groups))
        for item in groups:
            if isinstance(item, LinkAttrs):
                print("res:", item.path,  " link:", item.link)

    def testGettingLinks(self):
        info = ArchiveOrg.get_url_info("http://susodigital.com", min_size=1, limit=-100)
        for item in info:
            link = ArchiveOrg.get_archive_link(item)
            print(link)

    def testGettingLinksVariation(self):
        test_pool = pool.ThreadPool(processes=100)
        url = "http://bbc.co.uk"
        latest = ArchiveOrg.get_url_info(url, min_size=1, limit=-1)[0]
        timestamp =""
        if isinstance(latest, ArchiveStruct):
            timestamp = latest.date_stamp

        info = ArchiveOrg.get_domain_urls(url, limit=2000)
        res_count = len(info)
        broken_res_count = 0
        links = []
        for item in info:
            item.date_stamp = timestamp
            links.append(ArchiveOrg.get_archive_link(item))
        results = [test_pool.apply_async(func=test_response, args=(x,)) for x in links]
        returned = [y.get() for y in results]
        for result in returned:
            if result == False:
                broken_res_count += 1
        print("total:", res_count, " broken res:", broken_res_count)

    def testLinkParameters(self):
        link = "http://web.archive.org/web/20141218102128/http://susodigital.com/template"
        paras = LinkUtility.get_link_detail(link)
        print(paras)

    def testRemoveFootPrint(self):
        footprint = "something good<!-- BEGIN WAYBACK TOOLBAR INSERT -->middle craps okafa <><!-- END WAYBACK TOOLBAR INSERT -->next item is here!"
        LinkUtility.remove_archive_org_footprint(footprint)

    def testRemoveFootprint2(self):
        link = "http://web.archive.org/web/20140711025724/http://susodigital.com/"
        page_source = LinkChecker.get_page_source(link)
        bs4_tree = LinkUtility.remove_archive_org_footprint(page_source.text)
        link_list = []
        for child in bs4_tree.find_all():
            if isinstance(child, bs4.Tag):
                if "href" in child.attrs:
                    link_list.append(child["href"])
                elif "src" in child.attrs:
                    link_list.append(child["src"])
        for item in link_list:
            print(item)

    def testPath(self):
        current_link = "/web/20130415001342/http://www.browserchoice.eu/"
        inner_link, domain, path, ext, args = LinkUtility.get_link_detail(current_link)
        if len(inner_link) > 0:
            file_path, ref_path = LinkUtility.make_valid_web_res_path(path)
            print("file_path:", file_path, "ref_path:", ref_path)

    def testScrapePage(self):
        link = "http://web.archive.org/web/20140711025724/http://susodigital.com/"
        #link ="http://web.archive.org/web/20130415001342/http://www.bbc.co.uk/"
        stop_event = multiprocessing.Event()
        inner_link, domain, path, ext, args = LinkUtility.get_link_detail(link)
        root_domain = LinkChecker.get_root_domain(domain)[1]
        path = "/index.html"
        link_s = LinkAttrs(link=link, path=path, ref_link="/", source=path, page_type=LinkUtility.EXT_WEBPAGE, level=0)
        explorer = ArchiveExplorer(original_domain=root_domain, link=link,
                                   external_stop_event=stop_event,
                                   download_base_dir=FilePath.get_default_archive_dir(), max_thread=10, max_level=2)
        explorer.run()