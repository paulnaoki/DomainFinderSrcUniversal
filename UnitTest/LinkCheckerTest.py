from urllib.parse import urlsplit
from DomainFinderSrc.Utilities import FilePath, FileIO
from unittest import TestCase
from DomainFinderSrc.Scrapers.LinkChecker import LinkChecker
from urllib import parse, robotparser
import shortuuid
from reppy.cache import RobotsCache
from DomainFinderSrc.Utilities.StrUtility import StrUtility


class LinkCheckerTest(TestCase):
    def testGetAgent(self):
        root_domain = "halifaxnational.com"
        agent = LinkChecker.get_robot_agent(root_domain)
        can_fetch = agent.can_fetch("*", "http://halifaxnational.com/somethin")
        print(agent,"can fetch:", can_fetch)

    def test_get_sub_domains(self):
        full_link = "http://blogspot.co.uk/"
        domain_data = LinkChecker.get_root_domain(full_link, False)
        root_domain = domain_data[1]
        sub_domain = domain_data[4]
        domain_suffix = domain_data[5]
        sub_domain_no_local = sub_domain.strip(domain_suffix)
        print(sub_domain_no_local)

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
        rp = LinkChecker.get_robot_agent("http://pointshound.com/robots.txt")
        if rp is not None:
            for i in range(1, 1000):
                print("count:", i, "can fetch:", rp.can_fetch("*", "http://www.bbc.co.uk/fafdjiaofpadpvhagaarga/news/agqrgfv/y"))
        else:
            print("domain is not available.")

    def testRobot3(self):
        robots = RobotsCache()
        rules = robots.fetch("http://www.realwire.com/")
        crawl_delay = rules.delay("idiot")
        print("delay is:", crawl_delay)
        for i in range(1, 1000):
            print(rules.allowed("http://api.google.com/search/", agent="idiot"))

    def testRobot4(self):
        #rules = LinkChecker.get_robot_agent("sbnet.se")
        rules = LinkChecker.get_robot_agent("realwire.com")
        crawl_delay = rules.delay("idiot")
        print("delay is:", crawl_delay)
        for i in range(1, 1000):
            print(rules.allowed("http://api.google.com/search/", agent="idiot"))

    def testRobot5(self):
        base_link = "http://pointshound.com"
        test_sub_paths = [
                         "/", "/why", "/about", "/privacy", "/howitworks", "/help",
                         "/press", "/terms", "/guarantee", "/contact_form", "/something-else"]
        rules = LinkChecker.get_robot_agent("pointshound.com", protocol="https")
        for item in test_sub_paths:
            path = base_link + item
            is_allowed = rules.allowed(path, agent="VegeBot Test")
            print("sub_path:", item, " is allowed:", is_allowed)




    def testShortUid(self):
        key = "susodigital"
        domain = "alfjaofjafjapdfja.com"
        encoded = StrUtility.encrypt_XOR(key=key, plaintext=domain)
        print(encoded)
        decoded = StrUtility.decrypt_XOR(key, encoded)
        print(decoded)

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

    def testRequest(self):
        url = "http://127.0.0.1:8000/"
        agent = "VegeBot"
        source = LinkChecker.get_page_source(url, agent=agent, from_src="abuse-report@terrykyleseoagency.com")
        print(source)

    def testRequestAllLink(self):
        url = "http://www.jehovahs-witness.com"
        agent = "VegeBot-Careful"
        source = LinkChecker.get_page_source(url, agent=agent, from_src="abuse-report@terrykyleseoagency.com", retries=0)
        links = LinkChecker.get_all_links_from_source(source)
        for link in links:
            paras = urlsplit(link)
            page_scheme, page_domain = paras[0], paras[1]
            print(LinkChecker.get_valid_link(page_domain, link.strip(), page_scheme))


