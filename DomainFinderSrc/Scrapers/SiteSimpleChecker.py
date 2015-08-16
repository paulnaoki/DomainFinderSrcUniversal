from DomainFinderSrc.Scrapers.SiteChecker import PageChecker, SiteChecker
from DomainFinderSrc.Scrapers.LinkChecker import ResponseCode


class SiteSimpleChecker(SiteChecker):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print("init siteSimpleChecker finished")

    def begin_crawl(self, level=0):
        """
        :return: True if finished successfully, else the crawler stopped, but may have results
        """
        print(self.domain, " get next level : ", str(level+1))
        pages = self.data_source.get_onsite_links(level+1, ResponseCode.LinkNotBroken) #+ self.get_onsite_links(level+1, ResponseCode.LinkRedirect)
        if pages is None or len(pages) == 0:  # end of crawling
            print(self.domain, " next level is None crawling stop at page: ", str(self.page_count), " level: ", str(level))
            return True
        else:
            for page in pages:
                if self.page_count >= self.max_page or level >= self.max_level:
                    print(self.domain, " reach limit crawling stop at page: "+str(self.page_count), " level: ", str(level))
                    return True
                try:
                    PageChecker.crawl_page(self, page)
                    self.page_count += 1
                except Exception as e:
                    print(self.domain + " " + page.link + " " + str(e))
            return True and self.begin_crawl(level + 1)  # crawl next level, recursive