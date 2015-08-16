from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement

from DomainFinderSrc.PageNavigator import Navigator
from DomainFinderSrc.Scrapers.WebDriver import WebDriver
from DomainFinderSrc.SiteConst import SiteAccount
from DomainFinderSrc.GoDaddyCom.Elements.BulkCheckElements import BulkCheckElements
from DomainFinderSrc.GoDaddyCom.Elements.CommonCheckElements import CommonCheckElement


class GoDaddyComConst:
    ExpiredDomainBulkCheckPage = "https://uk.godaddy.com/bulk-domain-search.aspx" # bulk check on some TLDs
    ExpiredDomainCommonCheckPage = "https://uk.godaddy.com/domains/domain-name-search.aspx" #check for almost all TLDs
    ExpiredDomainBulkCheckLimit = 500


class DomainType:
    Expired = 1
    Taken = 2
    NotKnown = 3

    def __init__(self, domain: str, status: int):
        self.domain = domain
        self.status = status

    def __str__(self):
        if self.status == DomainType.Expired:
            return self.domain + " Expired"
        elif self.status == DomainType.Taken:
            return self.domain + " Taken"
        else:
            return self.domain + " Not Known"


class DomainCheckResult:
    def __init__(self, domain_name: str, domain_type: DomainType, price: float, currency: str):
        self.domain = domain_name
        self.domain_type = domain_type
        self.price = price
        self.currency = currency

    def __str__(self):
        return "%s %s %.2f" % (str(self.domain_type), self.currency, self.price)


class GoDaddy:
    def __init__(self, account: SiteAccount=None):
        self.account = account
        self.ExpiredBulkDomainCheck = GoDaddyComConst.ExpiredDomainBulkCheckPage
        self.ExpiredCommonDomainCheck = GoDaddyComConst.ExpiredDomainCommonCheckPage

        self.resultList = []

    def load_for_expired_domains_check_common(self, rawData:[]) ->[]:
        """
        Check domain one by one, this is suitable for all TLDs
        :param rawData: a list of root domains
        :return: a list of expired domains in DomainCheckResult format, or empty [] if nothing found
        """
        results = []
        if rawData is not None and len(rawData) > 0:
            self.driver = WebDriver.get_chrome()
            nav = Navigator(self.driver)
            counter = 0
            #inputBox = nav.checkPage(self.ExpiredCommonDomainCheck,CommonCheckElement.get_element(CommonCheckElement.id_domains_input_field), 10)
            while counter < len(rawData):
                inputBox = nav.checkPage(self.ExpiredCommonDomainCheck,CommonCheckElement.get_element(CommonCheckElement.id_domains_input_field), 10)
                product_list = None
                domain = rawData[counter]
                inputBox.send_keys(rawData[counter])
                #if counter == 0:
                try:
                    product_list = nav.checkClickAction(CommonCheckElement.get_element(CommonCheckElement.css_search_button),
                                                        CommonCheckElement.get_element(CommonCheckElement.css_product_list), 10)
                except:
                    pass
                #else:
                    #nav.get_element(CommonCheckElement.get_element(CommonCheckElement.id_search_again_btn)).click()
                    #product_list = nav.checkPage("", CommonCheckElement.get_element(CommonCheckElement.id_product_list), 10 )
                    #product_list = nav.checkClickAction(CommonCheckElement.get_element(CommonCheckElement.id_search_again_btn),
                    #                                    CommonCheckElement.get_element(CommonCheckElement.id_product_list), 10)
                digits = 9999999.00
                currency = "@"
                target = None
                if product_list is not None:
                    available = nav.get_element(CommonCheckElement.get_element(CommonCheckElement.css_available_target))
                    if available is not None and available.is_displayed():
                        product = Navigator.get_element_static(product_list, CommonCheckElement.get_element(CommonCheckElement.class_product_name))
                        domain_name = str(product.text).replace("\n","")
                        if product is None or domain_name != domain:
                            counter += 1
                            continue
                        prices = Navigator.get_elements_static(product_list,CommonCheckElement.get_element(CommonCheckElement.css_domain_price))
                        if prices is None:
                            counter += 1
                            continue
                        #print(domain + "is good")
                        len_price = len(prices)
                        if len_price > 2:
                            len_price = 2
                        for item in prices[:len_price]:
                            price = item.text
                            if len(price) < 1:
                                counter += 1
                                continue
                            price = price.strip()
                            if price.endswith("*"):
                                price = price.rstrip("*")
                            temp = float(price[1:])
                            if temp < digits:
                                digits = temp
                            currency = price[0]
                        target = DomainCheckResult(domain, DomainType(domain, DomainType.Expired), digits, currency)
                        print(target)
                    else:
                        target = DomainCheckResult(domain, DomainType(domain, DomainType.Taken), digits, currency)
                    #print(target)
                    results.append(target)
                else:
                    counter += 1
                    continue
                #inputBox = nav.get_element(CommonCheckElement.get_element(CommonCheckElement.id_domains_input_again_field))
                #inputBox.clear()
                counter += 1


        return results

    def load_for_expired_domains_bulk_check(self, rawData: []) ->[]:
        """
        Bulk check with a list of domains for some type of TLDs, other wise you have to do load_for_expired_domains_check_common()
        :param rawData: a list of root domains
        :return: a list of exprired domains, or None if nothing found
        """
        if rawData is not None and len(rawData) > 0:
            self.driver = WebDriver.get_chrome()
            nav = Navigator(self.driver)
            inputBox = nav.checkPage(self.ExpiredBulkDomainCheck, BulkCheckElements.get_element_by_id(BulkCheckElements.id_domains_input_field), 20)
            checkCount = 0
            navChain =[BulkCheckElements.get_element_by_id(BulkCheckElements.id_search_button),
                       BulkCheckElements.get_element_by_id(BulkCheckElements.id_check_out_button),
                       BulkCheckElements.get_element_by_class(BulkCheckElements.class_cart_products)]
            if inputBox is not None:
                inputBox.clear()  # clear the text area
                while checkCount < len(rawData):
                    for item in rawData:
                        inputBox.send_keys(item)
                        inputBox.send_keys(Keys.RETURN)
                        checkCount += 1
                resultTable = nav.checkClickActionChain(navChain, 60)
                result = self.parse_results_for_bulk_expired_domains_search(resultTable)
                self.resultList += result
                return result
            else:
                return None
        else:
            return None

    @staticmethod
    def checkAvailability(text: str) -> int:
        if text is not None:
            if BulkCheckElements.get_return_msg(BulkCheckElements.msg_domain_avaiable) in text:
                return DomainType.Expired
            else:
                return DomainType.Taken
        else:
            return DomainType.NotKnown

    def parse_results_for_bulk_expired_domains_search(self, element: WebElement) ->[]: #return a list of DomainType
        if element is not None:
            products = element.find_elements_by_class_name(BulkCheckElements.get_element_by_class(BulkCheckElements.class_product).target)
            filtered = []
            for product in products:
                domain = product.find_element_by_class_name(BulkCheckElements.get_element_by_class(BulkCheckElements.class_domain_name).target).text
                available = GoDaddy.checkAvailability(product.find_element_by_class_name(
                    BulkCheckElements.get_element_by_class(BulkCheckElements.class_msg).target).text)
                filtered.append(DomainType(domain, available))
            return filtered
        else:
            return None

    def get_result(self):  # return a list of DomainType
        return self.resultList



