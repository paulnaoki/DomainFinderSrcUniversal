from DomainFinderSrc.Utilities import FilePath, FileIO
from unittest import TestCase
from DomainFinderSrc.Scrapers.LinkChecker import LinkChecker
from urllib import parse, robotparser
import shortuuid


class LinkCheckerTest(TestCase):
    def testGetAgent(self):
        root_domain = "iristronics.com"
        agent = LinkChecker.get_robot_agent(root_domain)
        can_fetch = agent.can_fetch("*", "http://iristronics.com/somethin")
        print(agent,"can fetch:", can_fetch)

    def test_get_all_links(self):
        link = "http://web.archive.org/web/20140711025724/http://susodigital.com/"
        source = LinkChecker.get_page_source(link)
        all_links = LinkChecker.get_all_links_from_source(source)
        for link in all_links:
            print(link)

    def testURLDECoding(self):
        test_url = "http://something/http%3A%2F%2Fpagead2.googlesyndication.com%2Fpagead%2Ficlk%3Fsa%3Dl%26ai%3DBXPqvlXhERb7wM"
        decoded = parse.unquote(test_url)
        print(decoded)

    def testRobot(self):
        rp = robotparser.RobotFileParser(url="http://www.bbc.co.uk/robots.txt")
        rp.read()
        for i in range(1, 1000):
            print("count:", i, "can fetch:", rp.can_fetch("*", "http://www.bbc.co.uk/news"))

    def testRobot2(self):
        rp = LinkChecker.get_robot_agent("bbc.co.uk")
        if rp is not None:
            for i in range(1, 1000):
                print("count:", i, "can fetch:", rp.can_fetch("*", "http://www.bbc.co.uk/fafdjiaofpadpvhagaarga/news/agqrgfv/y"))
        else:
            print("domain is not available.")

    def testShortUrl1(self):
        # url = "/web/20130603113639/http://gamblingaddiction.cc/salendine-%e0%b8%99%e0%b8%b8%e0%b9%8a%e0%b8%81%e0%b8%a5%e0%b8%b4%e0%b8%99%e0%b8%94%e0%b9%8c%e0%b8%a1%e0%b8%b2%e0%b8%a3%e0%b9%8c%e0%b8%8a%e0%b8%82%e0%b9%88%e0%b8%b2%e0%b8%a7%e0%b8%a3%e0%b8%b4%e0%b8%9f.html"
        # url = "/salendine-%e0%b8%99%e0%b8%b8%e0%b9%8a%e0%b8%81%e0%b8%a5%e0%b8%b4%e0%b8%99%e0%b8%94%e0%b9%8c%e0%b8%a1%e0%b8%b2%e0%b8%a3%e0%b9%8c%e0%b8%8a%e0%b8%82%e0%b9%88%e0%b8%b2%e0%b8%a7%e0%b8%a3%e0%b8%b4%e0%b8%9f.html"
        url = "http://gamblingaddiction.cc/salendine-%e0%b8%99%e0%b8%b8%e0%b9%8a%e0%b8%81%e0%b8%a5%e0%b8%b4%e0%b8%99%e0%b8%94%e0%b9%8c%e0%b8%a1%e0%b8%b2%e0%b8%a3%e0%b9%8c%e0%b8%8a%e0%b8%82%e0%b9%88%e0%b8%b2%e0%b8%a7%e0%b8%a3%e0%b8%b4%e0%b8%9f.html"
        # shortened = short_url.encode_url(url)
        # print(shortened)
        # extended = short_url.decode_url(shortened)
        # print(extended)
        shorter = shortuuid.ShortUUID()
        shortened = shorter.uuid(name=url)
        print(shortened)
        extended = shorter.decode(shortened)
        print(extended)

    def testShortUrl2(self):
        urls = ["http://gamblingaddiction.cc/salendine-%e0%b8%99%e0%b8%b8%e0%b9%8a%e0%b8%81%e0%b8%a5%e0%b8%b4%e0%b8%99%e0%b8%94%e0%b9%8c%e0%b8%a1%e0%b8%b2%e0%b8%a3%e0%b9%8c%e0%b8%8a%e0%b8%82%e0%b9%88%e0%b8%b2%e0%b8%a7%e0%b8%a3%e0%b8%b4%e0%b8%9f.html",
                "/salendine-%e0%b8%99%e0%b8%b8%e0%b9%8a%e0%b8%81%e0%b8%a5%e0%b8%b4%e0%b8%99%e0%b8%.html",
                "/salendine-%e0%b8%99%e0%b8%b8%e0%b9%8a%e0%b8%81%e0%b8%a5%e0%b8%b4%e0%b8%99%e0%b8%",
                "/中国人民解放军/中国人民解放军/中国人民解放军.html",
                "strongholeqp4tfq;eafak;faf"]
        for url in urls:
            short_path, ext = LinkChecker.get_shorter_url_path(url)
            print("doing:", url)
            print("new path:", short_path)
            print("extension:", ext)



