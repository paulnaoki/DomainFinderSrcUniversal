import sqlite3
from DomainFinderSrc.Utilities.FilePath import get_temp_db_dir
from DomainFinderSrc.Utilities.Serializable import Serializable


class DBFilterInterface(Serializable):
    def __init__(self, update_interval=10):
        self.update_interval = update_interval

    def need_filtering(self):
        return False

    def __eq__(self, other):
        members = [attr for attr in dir(other) if not callable(getattr(other, attr)) and not attr.startswith("__") and
                   not attr == "update_interval"]
        counter = 0
        for member in members:
            other_obj = getattr(other, member)
            member_obj = getattr(self, member)
            counter += 1
            if member_obj is None:
                return False
            else:
                if other_obj == member_obj:
                    if counter == len(members):
                        return True
                    else:
                        continue
                else:
                    return False


class SeedSiteFilter(DBFilterInterface):
    def __init__(self, min_page=0, update_interval=1000):
        DBFilterInterface.__init__(self, update_interval=update_interval)
        self.min_page = min_page

    def need_filtering(self):
        if self.min_page > 0:
            return True
        else:
            return False


class FilteredResultFilter(DBFilterInterface):
    def __init__(self, tf=0, cf=0, da=0, arc=0, price=0.0, ref_domains=0, backlinks=0, update_interval=100):
        DBFilterInterface.__init__(self, update_interval=update_interval)
        self.tf = tf
        self.cf = cf
        self.da = da
        self.arc = arc  # archive count
        self.price = price
        self.ref_domains = ref_domains
        self.backlinks = backlinks

    def need_filtering(self):
        if self.tf > 0 or self.cf > 0 or self.da > 0 or self.arc > 0 or self.ref_domains > 0 or self.backlinks > 0:
            return True
        else:
            return False


class ExternalSiteDBFilter(DBFilterInterface):
    SignGr = ">="
    SignLs = "<="
    SignEq = "=="

    def __init__(self, code=0, update_interval=2, sign=">="):
        DBFilterInterface.__init__(self, update_interval=update_interval)
        self.code = code
        self.sign = sign

    def need_filtering(self):
        if self.code > 0:
            return True
        else:
            return False


class DBFilterCollection(Serializable):
    def __init__(self, seed=SeedSiteFilter(), external=ExternalSiteDBFilter(),
                 filteredResult=FilteredResultFilter(), save=False):
        self.seed_filter = seed
        self.external_filter = external
        self.filtered_result = filteredResult
        self.save = save

    def __eq__(self, other):
        if isinstance(other, DBFilterCollection):
            if self.seed_filter == other.seed_filter and self.external_filter == other.external_filter and self.filtered_result == other.filtered_result:
                return True
            else:
                return False
        else:
            return False


class SettingInfo(Serializable):
    def __init__(self, db_filter=DBFilterCollection()):
        self.db_filter = db_filter


class UserAccountDB:
    def __init__(self, company: str):
        DB_prefix = get_temp_db_dir()
        DB_name = "UserSettings"
        #AccountTabName = "Account"
        #SettingTabName = "Settings"
        self.company = company
        self.db = sqlite3.connect(DB_prefix+DB_name)
        self.cur = self.db.cursor()

    def get_setting_info(self) -> SettingInfo: # need to improve this function
        cmd = u"SELECT * FROM Settings WHERE Company=\'{0:s}\';".format(self.company,)
        cur = self.cur.execute(cmd)
        data = cur.fetchone()
        self.db.commit()
        if data is not None and len(data) > 0:
            settings = SettingInfo(data[0])
            try:
                if data[1] is not None:
                    settings.db_filter = Serializable.get_deserialized_json(data[1])
            except:
                pass
            return settings
        else:
            return None

    def set_filter(self, db_filters: DBFilterCollection):
        db_filter_str = db_filters.get_serializable_json()
        self.cur.execute(u"UPDATE Settings SET DB_FILTER=\'{0:s}\' WHERE Company=\'{1:s}\';".format(db_filter_str, self.company))
        self.db.commit()

    def close(self):
        self.db.close()