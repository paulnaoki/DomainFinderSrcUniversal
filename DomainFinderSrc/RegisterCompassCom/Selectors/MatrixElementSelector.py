from selenium import webdriver
from selenium.webdriver.support.ui import Select

from DomainFinderSrc.PageNavigator import SelecElement


class MatrixCompareCondition:
    greater = 0
    equal = 1
    lesser = 2


class MatrixElementSelector:

    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver

    def set_text_input(self, element: SelecElement, txt: str):
        element = self.driver.find_element_by_id(element.target)
        element.send_keys(txt)

    def set_element_checked(self, element: SelecElement):
        targetElement = self.driver.find_element_by_id(element.target)
        assert targetElement.get_attribute('type') == 'checkbox'
        targetElement.click()

    def set_element_range(self, element_equality: SelecElement, element_range_num: SelecElement, range_number: int,
                          condition=MatrixCompareCondition.greater):
        """
        :param element_equality_id:  The id has <option> tags and > or < or = sign
        :param element_range_num_id: The id has <input> tag and input is a number
        :param range_number: a number
        :return:
        """
        targetElement = Select(self.driver.find_element_by_id(element_equality.target))
        targetElement.select_by_index(condition)
        rangeElement = self.driver.find_element_by_id(element_range_num.target)
        rangeElement.send_keys(str(range_number))
