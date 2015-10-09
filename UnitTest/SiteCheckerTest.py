from unittest import TestCase
from DomainFinderSrc.Scrapers.SiteThreadChecker import SiteThreadChecker


class SiteCheckerTest(TestCase):
    def testThreadChecker(self):
        link = "http://training.seobook.com/tracking-results/"
        #link = "http://susodigital.com"
        checker = SiteThreadChecker(full_link=link, thread_pool_size=2, max_page=1000, max_level=10)
        checker.crawling()
