from UnitTest.Accounts import moz_count
from DomainFinderSrc.MozCom import *
from unittest import TestCase
from DomainFinderSrc.SiteConst import *
import csv
from DomainFinderSrc.SiteConst import _InternalAccountDB


class MozTest(TestCase):
    def testDA(self):
        moz = MozCom(moz_count)
        da = moz.get_ranking_data("")
        print("da:", da)

    def testDA_bulk(self):
        data_counter = 0
        domains = []
        data_path = "/Users/superCat/Desktop/PycharmProjectPortable/test/03-09-2015-Bad-Results.csv"
        with open(data_path, mode='r', newline='') as csv_file:
            rd = csv.reader(csv_file, delimiter=',')
            for row in rd:
                if data_counter > 0:
                    domains.append(row[0])
                data_counter += 1
        problem_account = [304, 578, 580, 606, 734, 741, 743]
        file_path = "/Users/superCat/Desktop/PycharmProjectPortable/test/accounts/Moz_Account.csv"
        count = 0
        with open(file_path, mode='r', newline='') as csv_file:
            reader = csv.reader(csv_file, delimiter=',')
            for email, psd, user_name, access_id, api_key in reader:
                if count in problem_account:
                    try:
                        print("email:", email, "psd:", psd, " user_name:", user_name, " access_id:", access_id,)
                        account = MozCom(SiteAccount(siteType=AccountType.Moz, userID=email, password=psd, AccessID=access_id, APIkey=api_key))
                        da = account.get_ranking_data(domains[count-20])
                        print("count: ", count, " access id:", access_id, " site:", domains[count], " da:", da)
                        time.sleep(0.2)
                    except Exception as ex:
                        print(ex)
                count += 1

    def testExport(self):
        db_path = "/Users/superCat/Desktop/PycharmProjectPortable/sync/"
        db = _InternalAccountDB(file_dir=db_path)
        file_path = "/Users/superCat/Desktop/PycharmProjectPortable/test/accounts/Moz_Account.csv"
        count = 0
        accounts = []
        with open(file_path, mode='r', newline='') as csv_file:
            reader = csv.reader(csv_file, delimiter=',')
            for email, psd, user_name, access_id, api_key in reader:
                print("email:", email, "psd:", psd, " user_name:", user_name, " access_id:", access_id,)
                account = SiteAccount(siteType=AccountType.Moz, userID=email, password=psd, AccessID=access_id, APIkey=api_key)
                accounts.append(account)
        db.add_accounts(accounts)



