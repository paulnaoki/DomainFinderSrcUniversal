import sqlite3
from DomainFinderSrc.Utilities.MachineInfo import MachineInfo, MachineType


def get_log_dir():
    WIN_PATH = "D:/SQLiteDB/Temp/Logging/"
    LINUX_PATH = "/tmp/Logging/"
    machine_type = MachineInfo.get_machine_type()
    return WIN_PATH if machine_type == MachineType.Windows else LINUX_PATH


def get_db_buffer_default_dir():
    machine_tpye = MachineInfo.get_machine_type()
    if machine_tpye == MachineType.Windows:
        temp_loc = "D:/SQLiteDB/Temp/DatabaseBuf/"
    else:
        temp_loc = "/tmp/DatabaseBuf/"
    return temp_loc


def get_temp_db_dir():
    DB_prefix = "/usr/local/DomainFinder/Database/"  # this is for Linux
    if MachineInfo.get_machine_type() == MachineType.Windows:
        DB_prefix = "D:/SQLiteDB/"
    return DB_prefix


def get_default_archive_dir():
    DB_prefix = "/usr/local/DomainFinder/Archive/"  # this is for Linux
    if MachineInfo.get_machine_type() == MachineType.Windows:
        DB_prefix = "D:/SQLiteDB/Archive/"
    return DB_prefix


def get_proxy_file_path():
    machine_tpye = MachineInfo.get_machine_type()
    if machine_tpye == MachineType.Windows:
        temp_loc = "D:/SQLiteDB/Temp/Proxy/proxy_list.csv"
    else:
        temp_loc = "/usr/local/DomainFinder/Database/proxy_list.csv"
    return temp_loc


def get_recovery_dir_path(ref: str=""):
    machine_tpye = MachineInfo.get_machine_type()
    if machine_tpye == MachineType.Windows:
        temp_loc = "D:/SQLiteDB/Temp/Recovery/"
    else:
        temp_loc = "/usr/local/DomainFinder/Recovery/"
    return temp_loc + ref


def get_task_backup_dir(ref: str=""):
    machine_tpye = MachineInfo.get_machine_type()
    if machine_tpye == MachineType.Windows:
        temp_loc = "D:/SQLiteDB/Temp/Task/"
    else:
        temp_loc = "/usr/local/DomainFinder/Task/"
    return temp_loc + ref


def get_download_file_path():
    if MachineInfo.get_machine_type() == MachineType.Windows:
        return 'D:/ChromeDownload/'
    else:
        return '/tmp/download/'


def get_chrome_exe_path():
    if MachineInfo.get_machine_type() == MachineType.Windows:
        return 'C:/WebDrivers/chromedriver.exe'
    else:
        return '/usr/lib/chromium-browser/chromedriver'


def get_spam_filter_keywords_file_path():
    keyword_file = "keywords.txt"
    if MachineInfo.get_machine_type() == MachineType.Windows:
        return 'D:/SQLiteDB/SpamFilter/' + keyword_file
    else:
        return '/usr/local/DomainFinder/SpamFilter/' + keyword_file


def get_spam_filter_anchors_file_path():
    anchor_file = "anchors.txt"
    if MachineInfo.get_machine_type() == MachineType.Windows:
        return 'D:/SQLiteDB/SpamFilter/' + anchor_file
    else:
        return '/usr/local/DomainFinder/SpamFilter/' + anchor_file


def get_spam_filter_bad_country_path():
    country_file = "bad_country.txt"
    if MachineInfo.get_machine_type() == MachineType.Windows:
        return 'D:/SQLiteDB/SpamFilter/' + country_file
    else:
        return '/usr/local/DomainFinder/SpamFilter/' + country_file

class SiteSource:
    """
    source used by DBInterface
    """
    Seed = "SeedSite"
    AllExternal = "AllExternal"
    Flitered = "Filtered"
    Filtered_bad = "Filtered_Bad"

    @staticmethod
    def get_default_address(source_type: str):
        DB_prefix = "/usr/local/DomainFinder/Database"  # this is for Linux
        if MachineInfo.get_machine_type() == MachineType.Windows:
            DB_prefix = "D:/SQLiteDB"
        if source_type == SiteSource.Seed:
            return DB_prefix + "/SeedSitesList"
        elif source_type == SiteSource.AllExternal:
            return DB_prefix + "/ResultSitesList"
        elif source_type == SiteSource.Flitered:
            return DB_prefix + "/FilteredSitesList"
        elif source_type == SiteSource.Filtered_bad:
            return DB_prefix + "/FilteredSitesList_Bad"
        else:
            return ":memory:"

    @staticmethod
    def get_all_table_names(source_type: str, address: str=None) -> []:
        addr = None
        if address is None:
            addr = SiteSource.get_default_address(source_type)
        else:
            addr = address
        db = sqlite3.connect(addr)
        cur = db.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type = \"table\"")
        db.commit()
        result = cur.fetchall()
        db.close()
        return [x for xa in result for x in xa]