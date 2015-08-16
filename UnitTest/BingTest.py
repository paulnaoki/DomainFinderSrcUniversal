from unittest import TestCase
from DomainFinderSrc.BingCom import *
from DomainFinderSrc.Scrapers.LinkChecker import *

from urllib import request
import csv
from io import StringIO
from pysimplesoap.client import SoapClient



class OnlineFileReader:
    @staticmethod
    def read_csv_file(link: str) -> []:
        response = request.urlopen(link)
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


class BingTest(TestCase):
    def testBacklinksData(self):
        testURL = "https://wmstat.bing.com/webmaster/data.ashx?wmkt=en-US&wlang=en-US&type=linkexplorer&linkurl=http://susodigital.com&url=" \
                  "&anchor=&query=&domain=true&source=1"

        client = SoapClient(wsdl="https://ssl.bing.com/webmaster/api.svc?wsdl")
        print(client)
