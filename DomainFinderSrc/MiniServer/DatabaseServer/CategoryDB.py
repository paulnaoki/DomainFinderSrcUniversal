import sqlite3
from DomainFinderSrc.MajesticCom.Category import *
from DomainFinderSrc.Utilities.Serializable import Serializable

# skeleton db


class SubCategoryStruct(Serializable):
    def __init__(self, sub_category: SubCategory=None, count: int=0):
        self.sub_category = sub_category
        self.count = count

    def to_tuple(self):
        return str(self.sub_category), self.count


class CategoryStruct(Serializable):
    def __init__(self, category_name: str="", sub_category_list: [SubCategoryStruct]=None):
        self.category_name = category_name
        self.sub_category = sub_category_list
        if self.sub_category is None:
            self.sub_category = []
        self.re_calcuate_stats()
        # if sub_category_list is not None:
        #     self.sub_category_names = [str(item.sub_category) for item in sub_category_list]
        #     self.sub_category_sum = sum([item.count for item in sub_category_list])
        # else:
        #     self.sub_category_names = []
        #     self.sub_category_sum = 0

    def re_calcuate_stats(self):
        self.sub_category_sum = sum([item.count for item in self.sub_category]) if self.sub_category is not None else 0
        self.sub_category_names = [str(item.sub_category) for item in self.sub_category] if self.sub_category is not None else []


class CategoryDB:
    def __init__(self, db_addr: str):
        self.db = sqlite3.connect(db_addr)
        self.cur = self.db.cursor()

    def get_main_category_tables_name(self) -> [str]:
        self.cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        results = self.cur.fetchall()
        if len(results) > 0:
            return [x[0] for x in results]
        else:
            return []

    def get_sub_category(self, category_table: str) -> [SubCategoryStruct]:
        results = []
        try:
            self.cur.execute("SELECT * FROM {0:s};".format(category_table,))
            temp = self.cur.fetchall()
            for sub_category, count in temp:
                results.append(SubCategoryStruct(CategoryManager.decode_sub_category(sub_category, False), count))
        except Exception as ex:
            print(ex)
        finally:
            return results

    def get_all_sub_categories(self) -> [SubCategoryStruct]:
        main_categories = self.get_main_category_tables_name()
        sub_categories = []
        for item in main_categories:
            sub_categories += self.get_sub_category(item)
        return sub_categories

    def save_sub_category(self, category_table: str, sub_category_list: [SubCategoryStruct]):
        try:
            self.cur.execute("CREATE TABLE IF NOT EXISTS \'{0:s}\'(SUB_CATEGORY TEXT, COUNT INTEGER, "
                             "PRIMARY KEY(SUB_CATEGORY));".format(category_table,))
            self.cur.executemany(u"INSERT OR REPLACE INTO \'{0:s}\' "
                                 u"(SUB_CATEGORY, COUNT) VALUES ( ?, ?);".format(category_table),
                                 [x.to_tuple() for x in sub_category_list])
            self.db.commit()
        except Exception as ex:
            print(ex)

    def close(self):
        self.db.close()


class CategoryDBManager:
    def __init__(self, db_addr=str):
        self.categories = [CategoryStruct]
        self.db_addr = db_addr
        self.populate_from_db()

    def populate_from_db(self):
        self.categories.clear()
        db = CategoryDB(self.db_addr)
        main_categories = db.get_main_category_tables_name()
        for item in main_categories:
            sub_category = db.get_sub_category(item)
            self.categories.append(CategoryStruct(item, sub_category))
        db.close()

    def save(self):
        db = CategoryDB(self.db_addr)
        for item in self.categories:
            if isinstance(item, CategoryStruct):
                db.save_sub_category(item.category_name, item.sub_category)
        db.close()

    def get_main_category_by_name(self, name: str) -> CategoryStruct or None:
        Found = None
        for item in self.categories:
            if item.category_name == name:
                Found = item
                break
        return Found

    def re_calculate_stats(self):
        for main_category in self.categories:
            if isinstance(main_category, CategoryStruct):
                main_category.re_calcuate_stats()

    def reset_category_count(self):
        for main_category in self.categories:
            if isinstance(main_category, CategoryStruct):
                for sub_item in main_category.sub_category:
                    if isinstance(sub_item, SubCategoryStruct):
                        sub_item.count = 0
                main_category.re_calcuate_stats()

    def get_sub_category(self, category: SubCategory) -> SubCategoryStruct:
        main_category = self.get_main_category_by_name(category.main_category)
        found = None
        if isinstance(main_category, CategoryStruct):
            category_name = str(category)
            for item in main_category.sub_category:
                if isinstance(item, SubCategoryStruct) and str(item) == category_name:
                    found = item
                    break
            if found is None:
                found = SubCategoryStruct(category)
                main_category.sub_category.append(found)
                main_category.sub_category_names.append(category_name)
        else:
            found = SubCategoryStruct(category)
            self.categories.append(CategoryStruct(category.main_category, [found, ]))

        return found