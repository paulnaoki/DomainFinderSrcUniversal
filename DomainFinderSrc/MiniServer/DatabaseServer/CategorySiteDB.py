from .CategoryDB import *
from DomainFinderSrc.MajesticCom.DataStruct import MajesticBacklinkDataStruct
import sqlite3
import threading
from DomainFinderSrc.Utilities.StrUtility import StrUtility
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
            category = StrUtility.make_valid_table_name(category)
            converted = [self.convert_input(x) for x in data]
            self.cur.execute(self.creation_query.format(category,))
            self.cur.executemany(self.insert_query.format(category,), converted)
            self.db.commit()
        except Exception as ex:
            print("error write to table:", category, " count:", len(data))
            print(ex)
            pass

    def get_total(self, category: str, **kvargs):
        count = 0
        try:
            category = StrUtility.make_valid_table_name(category)
            parameters_str = self.convert_filter(kvargs)
            query = "SELECT COUNT(*) FROM \'{0:s}\' "+parameters_str+";"
            self.cur.execute(query.format(category,))
            count = self.cur.fetchone()[0]
        except Exception as ex:
            print(ex)
        finally:
            return count

    def get_from_table(self, category: str, index: int, length: int, filter_dict: dict=None, reverse_read=True,
                       random_read=True) -> []:
        output = []
        reverse_read_clause = "DESC " if reverse_read else ""
        random_read_clause = "RANDOM()" if random_read else "rowid"
        try:
            category = StrUtility.make_valid_table_name(category)
            self.cur.execute(u"SELECT * FROM \'{0:s}\' {1:s} "
                             u"ORDER BY {2:s} {3:s}LIMIT {4:d} OFFSET {5:d};"
                             .format(category, CategorySiteDBInterface.convert_filter(filter_dict),
                                     random_read_clause, reverse_read_clause, length, index))
            output = [self.convert_output(x) for x in self.cur.fetchall()]
        except Exception as ex:
            print(ex)
        finally:
            return output

    def close(self):
        self.db.close()


class SeedDBRequest(Serializable):
    def __init__(self, niche="", random_read=True, reverse_read=True, data_len=0, tf=0, cf=0):
        self.niche = niche
        self.random_read = random_read
        self.reverse_read = reverse_read
        self.data_len = data_len
        self.tf, self.cf = tf, cf


class CategorySeedSiteDB(CategorySiteDBInterface):

    def __init__(self, db_path: str):
        creation_query = u"CREATE TABLE IF NOT EXISTS \'{0:s}\'" \
                         u"(DOMAIN TEXT, TF INTEGER, CF INTEGER, TROPICAL_TF INTEGER, COUNTRY TEXT, PO_URL INTEGER, PRIMARY KEY(DOMAIN));"
        insert_query = u"INSERT OR REPLACE INTO \'{0:s}\' (DOMAIN, TF, CF, TROPICAL_TF, COUNTRY, PO_URL) VALUES (?, ?, ?, ?, ?, ?);"
        #retrieve_query = u"SELECT DOMAIN, TF, CF, TROPICAL_TF FROM "
        CategorySiteDBInterface.__init__(self, db_path=db_path, creation_query=creation_query, insert_query=insert_query)

    def convert_input(self, obj):
        if isinstance(obj, tuple) and len(obj) == 6:
            return obj
        elif isinstance(obj, MajesticBacklinkDataStruct):
            return obj.ref_domain, obj.src_tf, obj.src_cf, obj.src_topic_tf, obj.country_code, obj.potential_url
        else:
            raise TypeError("type of the obj is wrong.")

    def convert_output(self, obj):
        if isinstance(obj, tuple) and len(obj) == 4:
            domain, tf, cf, topic_tf = obj
            return MajesticBacklinkDataStruct(ref_domain=domain, src_tf=tf, src_cf=cf, src_topical_tf=topic_tf)
        elif isinstance(obj, tuple) and len(obj) == 6:
            domain, tf, cf, topic_tf, country, potiental_url = obj
            return MajesticBacklinkDataStruct(ref_domain=domain, src_tf=tf, src_cf=cf, src_topical_tf=topic_tf, country_code=country, potential_url=potiental_url)
        else:
            raise TypeError("type of the obj is wrong.")


class CategorySiteDBManager:
    def __init__(self, db_class, **db_para):
        assert db_class is not None, "db_class is None."
        self._db_class = db_class
        self._db_para = db_para
        self._max_site_limit = 5000
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
            db = self._db_class(**self._db_para)
            data_len = len(self._temp_buff)
            if isinstance(db, CategorySiteDBInterface):
                for item in self._temp_buff:
                    db.save_to_table(item.sub_category_name, item.data_list)
                db.close()
            self._temp_buff = self._temp_buff[data_len-1:]
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
        except Exception as ex:
            pass
