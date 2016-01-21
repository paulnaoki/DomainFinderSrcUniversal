from urllib import request
import csv
from io import StringIO

from DomainFinderSrc.PageNavigator import Navigator
from DomainFinderSrc.SiteConst import SiteAccount
from DomainFinderSrc.Scrapers.WebDriver import WebDriver
from DomainFinderSrc.RegisterCompassCom.Elements.DNElements import DNElements
from DomainFinderSrc.RegisterCompassCom.Elements.TLDElement import RegTLD
from DomainFinderSrc.RegisterCompassCom.Elements.MajesticElements import MajesticElements
from DomainFinderSrc.RegisterCompassCom.Elements.SearchActionElements import DownloadActionElements
from DomainFinderSrc.RegisterCompassCom.Selectors.MatrixElementSelector import MatrixCompareCondition, MatrixElementSelector
# from DomainFinderSrc import xlrd


class ReCompConst:
    DomainSearchPage = "http://member.registercompass.com/member/DomainSearch.aspx"


class RegComp:
    def __init__(self, account: SiteAccount):
        self.account = account
        self.driver = WebDriver.get_chrome()

    def login(self):
        self.driver.get(self.account.siteLink)
        self.driver.find_element_by_id('ctl00_IdHeaderTopNavi_txt_user').send_keys(self.account.userID)
        self.driver.find_element_by_id('ctl00_IdHeaderTopNavi_txt_password').send_keys(self.account.password)
        self.driver.find_element_by_id('ctl00_IdHeaderTopNavi_lb_login').click()

    def goto_domain_search_page_and_set_filter(self, keyword: str):
        nav = Navigator(self.driver)
        nav.checkPage(ReCompConst.DomainSearchPage, RegTLD.get_tld_id(RegTLD.tld_com))
        if nav is not None:  # returned value is WebElement
            selector = MatrixElementSelector(self.driver)
            # select top level domains
            selector.set_element_checked(RegTLD.get_tld_id(RegTLD.tld_com))  # .com
            selector.set_element_checked(RegTLD.get_tld_id(RegTLD.tld_org))  # .org
            selector.set_element_checked(RegTLD.get_tld_id(RegTLD.tld_net))  # .net
            selector.set_element_checked(RegTLD.get_tld_id(RegTLD.tld_info))  # .info
            selector.set_element_checked(RegTLD.get_tld_id(RegTLD.tld_biz))  # .biz
            # select majestic matrix : trust flow and citation flow > 5
            selector.set_element_range(MajesticElements.get_element_id(MajesticElements.CitationFlowSign),
                                       MajesticElements.get_element_id(MajesticElements.CitationFlowNumber),
                                       5, MatrixCompareCondition.greater)
            selector.set_element_range(MajesticElements.get_element_id(MajesticElements.TrustFlowSign),
                                       MajesticElements.get_element_id(MajesticElements.TrustFlowNumber),
                                       5, MatrixCompareCondition.greater)
            # set the keyword
            if keyword is not None:
                selector.set_text_input(DNElements.get_element_id(DNElements.keywordField), keyword)

    def get_result_download_link(self) -> str:
        nav = Navigator(self.driver)
        idChainPre = [DownloadActionElements.get_element_id(DownloadActionElements.SearchButton),
                      DownloadActionElements.get_element_id(DownloadActionElements.ExpiredDomainExcel),
                      DownloadActionElements.get_element_id(DownloadActionElements.DownloadPageFrame),
                      ]

        innerFrame = nav.checkClickActionChain(idChainPre, 60)
        self.driver.switch_to.frame(innerFrame)
        idChainAfter = [DownloadActionElements.get_element_id(DownloadActionElements.DownloadResButton),
                        DownloadActionElements.get_element_id(DownloadActionElements.FinalDownloadBut),
                        ]
        element = nav.checkClickActionChain(idChainAfter, 60)
        self.downloadLink = element.find_element_by_tag_name("a").get_attribute("href")
        self.driver.switch_to_default_content()
        return self.downloadLink

    # def parse_result_using_xrld(self) -> []:
    #     if self.downloadLink is not None:
    #         response = request.urlopen(self.downloadLink)
    #         content = response.read()
    #         workbook = xlrd.open_workbook(self.downloadLink, file_contents=content)
    #         worksheet = workbook.sheet_by_index(0)
    #         num_rows = worksheet.nrows - 1
    #         curr_row = -1
    #         domainList = []
    #         while curr_row < num_rows:
    #             curr_row += 1
    #             if curr_row > 1:
    #                 domain = worksheet.cell_value(curr_row, 0)
    #                 domainList.append(domain)
    #                 print(domain)
    #         return domainList

    def parse_result_csv(self) -> []:  # use this
        if self.downloadLink is not None:
            response = request.urlopen(self.downloadLink)
            f = StringIO(response.read().decode('utf-8'))
            rowList = f.readlines()
            csv_f = csv.reader(rowList, delimiter="\t")
            # columns = [0]
            dataSize = len(rowList)
            resultList = []
            counter = 0
            if dataSize > 1:
                for row in csv_f:
                    if counter > 0:
                        resultList.append(row[0])
                    counter += 1
                return resultList
            else:
                return None








    def loadFile(self, filePath: str):
        self.driver.get("file:///" + filePath)

    def select(self):
        pass

    def get_driver(self):
        return self.driver
