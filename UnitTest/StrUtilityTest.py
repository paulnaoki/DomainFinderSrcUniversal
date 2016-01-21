from DomainFinderSrc.Utilities.StrUtility import StrUtility
from unittest import TestCase


class StrUtilityTest(TestCase):
    def testEscape(self):
        target_strs = ["women's toy", "2015/03/04 marketing"]
        for item in target_strs:
            print("before:", item, " after:", StrUtility.make_valid_table_name(item))

    def testStrIn(self):
        test_list = ['good', 'boy', 'eat', 'school']
        target = 'i went to school last night'
        if any(x in target for x in test_list):
            print("is in.")
        else:
            print("not in.")
