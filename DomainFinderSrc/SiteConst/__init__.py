import sqlite3
from DomainFinderSrc.Utilities.FileIO import FileHandler
from DomainFinderSrc.Utilities.FilePath import get_temp_db_dir


class SiteAccount:
    def __init__(self, siteType: int, userID: str, password: str="", siteLink: str="", AccessID: str=None, proxy: str="",
                 APIkey: str=None):
        self.siteType = siteType
        self.userID = userID
        self.password = password
        self.siteLink = siteLink
        self.APIKey = APIkey      #used by Moz.com
        self.AccessID = AccessID  # used by Moz.com
        self.proxy = proxy
        self.Available = True

    def __str__(self):
        return str(self.__dict__)


class AccountType:
    RegisterCompass = 1
    Ahrefs = 2
    Moz = 3
    ExpiredDomainNet = 4
    Majestic = 5
    Semrush = 6
    AmazonEC2 = 7
    Unknown = 99

    @staticmethod
    def get_site_name(siteType: int) -> str:
            return{
                AccountType.RegisterCompass: "RegisterCompassCom",
                AccountType.Ahrefs: "AhrefsCom",
                AccountType.Moz: "Moz",
                AccountType.ExpiredDomainNet: "ExpiredDomainNet",
                AccountType.Majestic: "Majestic",
                AccountType.Semrush: "Semrush",
                }.get(siteType, "NotSupported")


class _InternalAccountDB:
    def __init__(self, file_dir: str="", file_name="UserAccounts.db"):
        if len(file_dir) == 0:
            file_dir = get_temp_db_dir()
        FileHandler.create_file_if_not_exist(file_dir)
        self._file_name = file_name
        file_path = file_dir + self._file_name
        self.db = sqlite3.connect(file_path)
        self.cur = self.db.cursor()
        self.cur.execute("CREATE TABLE IF NOT EXISTS ACCOUNTS(TYPE INTEGER, USER_ID TEXT, PSD TEXT,"
                         " LINK TEXT,ACCESS_ID TEXT, API_KEY TEXT, PROXY TEXT);")
        self.db.commit()

    def add_accounts(self, accounts: []) -> bool:
        converted = []
        try:
            if accounts is not None and len(accounts) > 0:
                for item in accounts:
                    if isinstance(item, SiteAccount):
                        converted.append((item.siteType, item.userID, item.password, item.siteLink, item.AccessID,
                                          item.APIKey, item.proxy))
                if len(converted) > 0:
                    self.cur.executemany("INSERT OR REPLACE INTO ACCOUNTS(TYPE, USER_ID, PSD, LINK, ACCESS_ID, API_KEY, PROXY) "
                                         "VALUES (?,?,?,?,?,?,?);", converted)
                    self.db.commit()
                return True
            else:
                return False
        except Exception as ex:
            print(ex)
            return False

    def get_accounts(self) -> []:
        converted = []
        try:
            cur = self.cur.execute("SELECT * FROM ACCOUNTS;")
            accounts = cur.fetchall()
            if len(accounts) > 0:
                for siteType, userID, password, siteLink, AccessID, APIKey, proxy in accounts:
                    converted.append(SiteAccount(siteType=siteType, userID=userID, password=password, siteLink=siteLink,
                                                 AccessID=AccessID, APIkey=APIKey, proxy=proxy))
        except:
            pass
        finally:
            return converted

    def close(self):
        try:
            self.db.close()
        except:
            pass


class AccountManager:
    def __init__(self, db_addr=""):
        db = _InternalAccountDB(file_dir=db_addr)
        self.AccountList = db.get_accounts()

    def get_accounts(self, accountTpye :int) -> []:
        """
        :param accountTpye: an enum type of AccountType.
        :return: a list of accounts type(SiteAccount) OR None
        """
        return [x for x in self.AccountList if x.siteType == accountTpye]

    def get_account(self, userID: str, accountTpye : int) -> SiteAccount:
        """
        :param userID: user id
        :param accountTpye: an enum type of AccountType.
        :return: an account OR None
        """
        list = [x for x in self.AccountList if x.accountType == accountTpye and x.userID == userID]
        if list is not None and len(list) > 0:
            return list[0]
        else:
            return None




