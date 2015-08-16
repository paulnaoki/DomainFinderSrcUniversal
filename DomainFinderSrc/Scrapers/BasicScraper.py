import urllib.request

from selenium import webdriver

from DomainFinderSrc.Scrapers import WebRequestCommonHeader


class BasicScraper:
    def __init__(self, link: str):
        self.browser = webdriver.Chrome('C:/WebDrivers/chromedriver.exe')
        self.link = link

    def get_page_source(self, timeout=10):
        req = urllib.request.Request(self.link, None, WebRequestCommonHeader.WebRequestCommonHeader.get_html_header())
        response = urllib.request.urlopen(req, None, timeout)
        return response.read().decode('utf-8')

    def get_page_source_broswer(self):  # good for browser simulation
        self.browser.get(self.link)
        return self.browser.page_source
