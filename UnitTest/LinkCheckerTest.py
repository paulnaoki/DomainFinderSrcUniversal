from DomainFinderSrc.Utilities import FilePath, FileIO
from unittest import TestCase
from DomainFinderSrc.Scrapers.LinkChecker import LinkChecker


class LinkCheckerTest(TestCase):
    def test_get_all_links(self):
        link = "http://web.archive.org/web/20140711025724/http://susodigital.com/"
        source = LinkChecker.get_page_source(link)
        all_links = LinkChecker.get_all_links_from_source(source)
        for link in all_links:
            print(link)