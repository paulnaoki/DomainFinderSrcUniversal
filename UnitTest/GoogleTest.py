from unittest import TestCase
from DomainFinderSrc.GoogleCom import GoogleCom, GoogleConst


class GoogleTest(TestCase):
    def testGetLlinks(self):
        sites = GoogleCom.get_sites("gambling")
        for item in sites:
            print(item)

