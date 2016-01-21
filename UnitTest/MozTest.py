from UnitTest.Accounts import moz_account, moz_account_fake
from unittest import TestCase
from DomainFinderSrc.SiteConst import *
import csv
from DomainFinderSrc.MozCom import *
from DomainFinderSrc.SiteConst import _InternalAccountDB
from DomainFinderSrc.Utilities.Logging import CsvLogger
import json
import math


class MozTest(TestCase):

    def testDA_patch(self):
        data_counter = 0
        domains = []
        limit = 50
        data_path = "/Users/superCat/Desktop/PycharmProjectPortable/test/17-09-2015-Bad-Results.csv"
        with open(data_path, mode='r', newline='') as csv_file:
            rd = csv.reader(csv_file, delimiter=',')
            for row in rd:
                if data_counter > 0:
                    domains.append(row[0])
                data_counter += 1
                if data_counter >= limit+1:
                    break
        moz = MozCom(moz_account)
        data = moz.get_ranking_data_batch(domains, limit)
        for item in zip(domains, data):
            print(item)

    def test_da_decode(self):
        da_str = '[{"pda":28.477901825008377},{"pda":11.678222365784801},{"pda":11.624535635559873},{"pda":11.348318935257158}]'
        jsoned = json.loads(da_str)
        for item in jsoned:
            print(int(round(float(item['pda']), 0)))

    def test_iter(self):
        import collections
        afaf = [1]
        print(isinstance(afaf, collections.Iterable))
        temp2 = list(afaf)
        print(isinstance(temp2, collections.Iterable))
        print(afaf*2)

    def testDA(self):
        moz = MozCom(moz_account)
        da = moz.get_ranking_data("")
        print("da:", da)

    def testDA_bulk(self):
        log_path = "/Users/superCat/Desktop/PycharmProjectPortable/test/accounts/good_accounts.csv"
        bad_log_path = "/Users/superCat/Desktop/PycharmProjectPortable/test/accounts/bad_accounts.csv"
        good_rows = []
        bad_rows = []
        data_counter = 0
        domains = []
        data_path = "/Users/superCat/Desktop/PycharmProjectPortable/test/03-09-2015-Bad-Results.csv"
        with open(data_path, mode='r', newline='') as csv_file:
            rd = csv.reader(csv_file, delimiter=',')
            for row in rd:
                if data_counter > 0:
                    domains.append(row[0])
                data_counter += 1
        problem_account = []
        file_path = "/Users/superCat/Desktop/PycharmProjectPortable/test/accounts/good_accounts_backup.csv"
        count = 0
        work_count = 0
        non_work_count = 0
        with open(file_path, mode='r', newline='') as csv_file:
            reader = csv.reader(csv_file, delimiter=',')
            for email, psd, user_name, access_id, api_key in reader:
                if count not in problem_account:
                    try:
                        print("email:", email, "psd:", psd, " user_name:", user_name, " access_id:", access_id,)
                        account = MozCom(SiteAccount(siteType=AccountType.Moz, userID=email, password=psd, AccessID=access_id, APIkey=api_key))
                        da = account.get_ranking_data(domains[count])
                        print("count: ", count, " access id:", access_id, " site:", domains[count], " da:", da)
                        time.sleep(0.2)
                        work_count += 1
                        good_rows.append((count+1, email, psd, user_name, access_id, api_key))
                    except Exception as ex:
                        bad_rows.append((count+1, email, psd, user_name, access_id, api_key))
                        print(ex)
                        non_work_count += 1
                count += 1
        CsvLogger.log_to_file_path(log_path, good_rows)
        CsvLogger.log_to_file_path(bad_log_path, bad_rows)
        print("total:", count, " worked:", work_count, " not-worked:", non_work_count)

    def testExport(self):
        db_path = "/Users/superCat/Desktop/PycharmProjectPortable/sync/"
        db = _InternalAccountDB(file_dir=db_path)
        file_path = "/Users/superCat/Desktop/PycharmProjectPortable/test/accounts/good_accounts.csv"
        count = 0
        accounts = []
        with open(file_path, mode='r', newline='') as csv_file:
            reader = csv.reader(csv_file, delimiter=',')
            for email, psd, user_name, access_id, api_key in reader:
                print("email:", email, "psd:", psd, " user_name:", user_name, " access_id:", access_id,)
                account = SiteAccount(siteType=AccountType.Moz, userID=email, password=psd, AccessID=access_id, APIkey=api_key)
                accounts.append(account)
        db.add_accounts(accounts)

    def testAccountPrint(self):
        db_path = "/Users/superCat/Desktop/PycharmProjectPortable/sync/"
        manager = AccountManager(db_path)
        accounts = manager.get_accounts(AccountType.Moz)
        counter = 0
        for account in accounts:
            print("count:", counter, " ",account)
            counter += 1



