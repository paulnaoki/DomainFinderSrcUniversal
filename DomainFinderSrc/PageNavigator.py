from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement


class NavEleType:
    IsClass = 1
    IsCssSelector = 2
    IsName = 3
    IsId = 4

class SelecElement:
    def __init__(self, targerName, targetType: int= NavEleType.IsId):
        self.target = targerName
        self.element_type = targetType

class Navigator:
    def __init__(self, driver: webdriver.Chrome):
        """
        :param driver: The driver will load the page then check an element with ID, see if it is exsit
        :return:
        """
        self.driver = driver

    @staticmethod
    def get_element_static(target_element: WebElement, verifier: SelecElement) -> WebElement:
        try:
            element = None
            if verifier.element_type == NavEleType.IsId:
                element = target_element.find_element_by_id(verifier.target)
            elif verifier.element_type == NavEleType.IsClass:
                element = target_element.find_element_by_class_name(verifier.target)
            elif verifier.element_type == NavEleType.IsCssSelector:
                element = target_element.find_element_by_css_selector(verifier.target)
            elif verifier.element_type == NavEleType.IsName:
                element = target_element.find_element_by_name(verifier.target)
            else:
                raise ValueError("Selector not Supported")
            return element
        except Exception as inst:
            print(type(inst))
            print(inst.args)
            return None

    def get_element(self, target_element: SelecElement) -> WebElement:
        try:
            element = None
            if target_element.element_type == NavEleType.IsId:
                element = self.driver.find_element_by_id(target_element.target)
            elif target_element.element_type == NavEleType.IsClass:
                element = self.driver.find_element_by_class_name(target_element.target)
            elif target_element.element_type == NavEleType.IsCssSelector:
                element = self.driver.find_element_by_css_selector(target_element.target)
            elif target_element.element_type == NavEleType.IsName:
                element = self.driver.find_element_by_name(target_element.target)
            else:
                raise ValueError("Selector not Supported")
            return element
        except Exception as inst:
            print(type(inst))
            print(inst.args)
            return None

    @staticmethod
    def get_elements_static(target_element: WebElement, verifier: SelecElement) ->[]:
        try:
            elements = None
            if verifier.element_type == NavEleType.IsId:
                elements = target_element.find_elements_by_id(verifier.target)
            elif verifier.element_type == NavEleType.IsClass:
                elements = target_element.find_elements_by_class_name(verifier.target)
            elif verifier.element_type == NavEleType.IsCssSelector:
                elements = target_element.find_elements_by_css_selector(verifier.target)
            elif verifier.element_type == NavEleType.IsName:
                elements = target_element.find_elements_by_name(verifier.target)
            else:
                raise ValueError("Selector not Supported")
            return elements
        except Exception as inst:
            print(type(inst))
            print(inst.args)
            return None

    def get_elements(self, target_element: SelecElement)-> []:
        try:
            elements = None
            if target_element.element_type == NavEleType.IsId:
                elements = self.driver.find_elements_by_id(target_element.target)
            elif target_element.element_type == NavEleType.IsClass:
                elements = self.driver.find_elements_by_class_name(target_element.target)
            elif target_element.element_type == NavEleType.IsCssSelector:
                elements = self.driver.find_elements_by_css_selector(target_element.target)
            elif target_element.element_type == NavEleType.IsName:
                elements = self.driver.find_elements_by_name(target_element.target)
            else:
                raise ValueError("Selector not Supported")
            return elements
        except Exception as inst:
            print(type(inst))
            print(inst.args)
            return None


    def checkPage(self, page_link: str, verifier: SelecElement, timeout: int=5) -> WebElement:
        """
        :param timeout: timeout if the page takes too long to load
        :param page_link: the link to the page the driver uses to load
        :param verifier: the element id the driver will use to check against
        :return: True if the page has been loaded successfully
        """
        if len(page_link) != 0:
            self.driver.get(page_link)
        try:
            element = None
            if verifier.element_type == NavEleType.IsId:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.ID, verifier.target))
                )
            elif verifier.element_type == NavEleType.IsClass:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.CLASS_NAME, verifier.target))
                )
            elif verifier.element_type == NavEleType.IsCssSelector:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, verifier.target))
                )
            elif verifier.element_type == NavEleType.IsName:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.NAME, verifier.target))
                )
            else:
                raise ValueError("Selector not Supported")
            return element
        except Exception as inst:
            print(type(inst))
            print(inst.args)
            return None

    def checkClickAction(self, target: SelecElement, verifier: SelecElement, timeout: int=5) -> WebElement:
        """
        :param target: the target where 'click' action will perform on
        :param verifier: the element id the driver will use to check against
        :param timeout: timeout if the page takes too long to load
        :param target_is_id: True if target element has 'id' attr, else has 'class' attr
        :return: the webElement of verifier if the action has been performed correctly
        """
        self.driver.implicitly_wait(timeout)

        if target.element_type == NavEleType.IsId:
            self.driver.find_element_by_id(target.target).click()
        elif target.element_type == NavEleType.IsClass:
            self.driver.find_element_by_class_name(target.target).click()
        elif target.element_type == NavEleType.IsCssSelector:
            self.driver.find_element_by_css_selector(target.target).click()
        elif target.element_type == NavEleType.IsName:
            self.driver.find_element_by_name(target.target).click()
        else:
            raise ValueError("Selector not Supported")


        if verifier.element_type == NavEleType.IsId:
            return self.driver.find_element_by_id(verifier.target)
        elif verifier.element_type == NavEleType.IsClass:
            return self.driver.find_element_by_class_name(verifier.target)
        elif verifier.element_type == NavEleType.IsCssSelector:
            return self.driver.find_element_by_css_selector(verifier.target)
        elif verifier.element_type == NavEleType.IsName:
            return self.driver.find_element_by_name(verifier.target)
        else:
            raise ValueError("Selector not Supported")


    # click through a list of elements of type SelecElment in elementList
    def checkClickActionChain(self, elementList: [], timeout: int=5) -> WebElement:
        if elementList is None or len(elementList) == 0:
            return None
        else:
            resultElement = None
            for i in range(len(elementList) - 1):
                print("click " + elementList[i].target + "should return " + elementList[i+1].target)
                resultElement = self.checkClickAction(elementList[i], elementList[i+1], timeout)
            return resultElement


