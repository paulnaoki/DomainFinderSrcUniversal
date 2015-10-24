from .CategoryDB import *
from DomainFinderSrc.MajesticCom.DataStruct import MajesticBacklinkDataStruct
import sqlite3
import threading

# seed db

class CategorySiteDBDataStruct:
    def __init__(self, sub_category_name: str=""):
        self.sub_category_name = sub_category_name
        self.data_list = []

    def append_to_list(self, data):
        if data is not None:
            self.data_list.append(data)


class CategorySiteDBInterface:
    DOAMIN_FILED = "DOMAIN"

    def __init__(self, db_path: str, creation_query: str, insert_query: str): #, retrieve_query: str):
        assert db_path is not None and len(db_path) > 0, "db_path cannot be None or empty"
        assert creation_query is not None and len(creation_query) > 0, "creation_query cannot be None or empty."
        self.db = sqlite3.connect(db_path)
        self.cur = self.db.cursor()
        self.creation_query = creation_query
        self.insert_query = insert_query
        #self.retrieve_query = retrieve_query

    def get_sub_category_tables_name(self) -> [str]:
        self.cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        results = self.cur.fetchall()
        if len(results) > 0:
            return [x[0] for x in results]
        else:
            return []

    def convert_input(self, obj) -> tuple:
        raise NotImplementedError

    def convert_output(self, obj):
        raise NotImplementedError

    @staticmethod
    def convert_filter(obj: dict) -> str:
        if obj is None or len(obj) == 0:
            return ""
        else:
            clause = "WHERE "
            for k, v in obj.items():
                clause += str(k) + " >= " + str(v) + " "
            return clause

    def save_to_table(self, category: str, data: []):
        try:
            converted = [self.convert_input(x) for x in data]
            self.cur.execute(self.creation_query.format(category,))
            self.cur.executemany(self.insert_query.format(category,), converted)
            self.db.commit()
        except Exception as ex:
            pass

    def get_total(self, category: str):
        count = 0
        try:
            self.cur.execute(u"SELECT COUNT(*) FROM \'{0:s}\';".format(category,))
            count = self.cur.fetchone()[0]
        except Exception as ex:
            pass
        finally:
            return count

    def get_from_table(self, category: str, index: int, length: int, filter_dict: dict=None) -> []:
        output = []
        try:
            self.cur.execute(u"SELECT * FROM \'{0:s}\' {1:s} "
                             u"ORDER BY rowid LIMIT {2:d} OFFSET {3:d};"
                             .format(category, CategorySiteDBInterface.convert_filter(filter_dict), length, index))
            output = [self.convert_output(x) for x in self.cur.fetchall()]
        except Exception as ex:
            pass
        finally:
            return output

    def close(self):
        self.db.close()


class CategorySeedSiteDB(CategorySiteDBInterface):

    def __init__(self, db_path: str):
        creation_query = u"CREATE TABLE IF NOT EXISTS \'{0:s}\'" \
                         u"(DOMAIN TEXT, TF INTEGER, CF INTEGER, TROPICAL_TF INTEGER, PRIMARY KEY(DOMAIN));"
        insert_query = u"INSERT OR IGNORE INTO \'{0:s}\' (DOMAIN, TF, CF, TROPICAL_TF) VALUES (?, ?, ?, ?);"
        #retrieve_query = u"SELECT DOMAIN, TF, CF, TROPICAL_TF FROM "
        CategorySiteDBInterface.__init__(self, db_path=db_path, creation_query=creation_query, insert_query=insert_query)

    def convert_input(self, obj):
        if isinstance(obj, tuple) and len(obj) == 4:
            return obj
        elif isinstance(obj, MajesticBacklinkDataStruct):
            return obj.ref_domain, obj.src_tf, obj.src_cf, obj.src_topic_tf
        else:
            raise TypeError("type of the obj is wrong.")

    def convert_output(self, obj):
        if isinstance(obj, tuple) and len(obj) == 4:
            domain, tf, cf, topic_tf = obj
            return MajesticBacklinkDataStruct(ref_domain=domain, src_tf=tf, src_cf=cf, src_topical_tf=topic_tf)



class CategorySiteDBManager:
    def __init__(self, db: CategorySiteDBInterface):
        assert db is not None, "db is None."
        self.db = db
        self._max_site_limit = 2000
        self._site_counter = 0
        self._temp_buff = []
        self._db_write_lock = threading.RLock()

    def get_sub_category_by_name(self, name: str) -> CategorySiteDBDataStruct or None:
        sub_category = None
        if name is None or len(name) == 0:
            return sub_category
        if len(self._temp_buff) > 0:
            for item in self._temp_buff:
                if item.sub_category_name == name:
                    sub_category = item
                    break
        if sub_category is None:
            sub_category = CategorySiteDBDataStruct(name)
            self._temp_buff.append(sub_category)
        return sub_category

    def _save_to_db_and_reset(self):
        with self._db_write_lock:
            for item in self._temp_buff:
                self.db.save_to_table(item.sub_category_name, item.data_list)
            self._temp_buff.clear()
            self._site_counter = 0

    def append_to_buff(self, data, category: str):
        if category is not None and len(category) > 0:
            sub_category = self.get_sub_category_by_name(category)
            if sub_category is not None:
                sub_category.append_to_list(data)
                self._site_counter += 1
            if self._site_counter >= self._max_site_limit:
                self._save_to_db_and_reset()

    def close(self):
        try:
            self._save_to_db_and_reset()
            self.db.close()
        except Exception as ex:
            pass
