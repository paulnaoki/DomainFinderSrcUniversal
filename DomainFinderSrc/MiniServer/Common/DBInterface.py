import sqlite3
import tldextract
from DomainFinderSrc.MiniServer.Common.SocketCommands import SeedSiteFeedback
from DomainFinderSrc.Scrapers.SiteTempDataSrc.DataStruct import FilteredDomainData, ScrapeDomainData
from DomainFinderSrc.UserAccountSettings.UserAccountDB import DBFilterInterface, SeedSiteFilter, FilteredResultFilter, \
    ExternalSiteDBFilter
from DomainFinderSrc.Utilities.FilePath import SiteSource
from DomainFinderSrc.Utilities.Logging import *
from DomainFinderSrc.Utilities.StrUtility import StrUtility


class DBType:
    Type_Seed = "Seed"
    Type_External = "External"
    Type_Filtered_Result = "FilteredResult"
    Type_Filtered_Result_Bad = "FilteredResult_Bad"
    Type_Marketplace = "Marketplace"
    Type_All = "All"


class DBInterface:
    """
    DB must have the field DOMAIN
    """
    def __init__(self, table: str, creation_query :str, insert_query: str="",
                 offset=0, databaseType: str=SiteSource.Seed,  db_addr: str=None,
                 db_filter: DBFilterInterface=None):
        if databaseType is None:
            raise ValueError("database type cannot be None")
        if db_addr is None:
            self.db_addr = SiteSource.get_default_address(databaseType)
        else:
            self.db_addr = db_addr
        self.tab = table
        self.encoded_tab = StrUtility.make_valid_table_name(table)
        self.db_type = databaseType
        if (self.db_addr is None or len(self.db_addr) == 0) and len(creation_query) > 0:
            self.db = sqlite3.connect(":memory:")
        else:
            self.db = sqlite3.connect(self.db_addr)
        self.cur = self.db.cursor()
        self.cur.execute(creation_query)
        self.db.commit()
        self.insert_query = insert_query
        self.offset = offset
        self.db_filter = db_filter
        self.output_format_tuple = False
        self.get_lock = threading.RLock()

    def drop_table(self):
        self.cur.execute("DROP TABLE \'%s\';" % (self.encoded_tab,))
        self.db.commit()

    def import_from_file(self, file_path: str):
        pass

    def convert_input(self, obj) -> tuple:
        return obj

    def convert_output(self, obj):
        return obj

    def add_sites(self, sites, skip_check=False):
        if len(sites) < 1:
            return
        if skip_check:
            need_to_add = sites
        else:
            need_to_add = []
        try:
            if not skip_check:
                need_to_add = [self.convert_input(x) for x in sites]
            self.cur.executemany(self.insert_query.format(self.encoded_tab, ), need_to_add)
            self.db.commit()
        except Exception as ex:
            print(ex)
            msg = "add_sites() " + self.tab
            ErrorLogger.log_error("SeedSiteDB", ex, msg)

    @staticmethod
    def get_fields_names():
        return "DOMAIN",

    def get_all_sites(self) ->[]:
        self.cur.execute("SELECT DOMAIN FROM \'%s\';" % (self.encoded_tab,))
        self.db.commit()
        return self.cur.fetchall()

    def is_domain_in_db(self, domain: str):
        try:
            cur = self.cur.execute("SELECT EXISTS(SELECT 1 FROM \'{0:s}\' "
                                   "WHERE DOMAIN=\'{1:s}\' LIMIT 1);".format(self.encoded_tab, domain,))
            #cur = tempdb.cur.execute("SELECT * FROM TEMP WHERE LINK=\'{0:s}\' LIMIT 1;".format(link,))
            result = cur.fetchone()
            return True if result[0] == 1 else False
        except sqlite3.OperationalError as ex:
            return True  # so that new data will not add to the db to cause further error

    @staticmethod
    def get_query_para(**para) -> dict:
        return {}

    def convert_query_para(self, **kwargs) -> str:
        return ""

    def get_next_patch_no_rollover(self, index: int, count: int, reverse_read=False,  **kwargs):
        reverse_read_clause = "DESC " if reverse_read else ""
        try:
            self.cur.execute(u"SELECT * FROM \'{0:s}\'{1:s} ORDER BY rowid {2:s}LIMIT {3:d} OFFSET {4:d};".
                             format(self.encoded_tab, self.convert_query_para(**kwargs), reverse_read_clause, count, index))
            results = [self.convert_output(x) for x in self.cur.fetchall()]
            return results

        except Exception as ex:
            raise ex

    def get_next_patch(self, count: int, rollover=True, **kwargs) ->[]:  # if you need a custom filtered implmentation
        result = []
        total = self.site_count()
        if count > total:
            count = total
        limit = 0
        if count + self.offset > total:
            limit = total - self.offset
        else:
            limit = count
        self.cur.execute("SELECT * FROM \'%s\' ORDER BY rowid LIMIT %d OFFSET %d" % (self.encoded_tab, limit, self.offset))
        self.db.commit()
        result += self.cur.fetchall()
        self.offset += limit
        if rollover and limit < count:
            new_limit = 0
            if count - limit > total:
                new_limit = total
            else:
                new_limit = count - limit
            self.cur.execute("SELECT * FROM \'%s\' ORDER BY rowid LIMIT %d OFFSET %d" % (self.encoded_tab, new_limit, 0))
            self.db.commit()
            result += self.cur.fetchall()
            self.offset = new_limit
        return result

    def site_count_with_filter(self):
        return 0

    def site_count(self, use_filter=True) -> int:
        if use_filter and self.db_filter is not None and self.db_filter.need_filtering():
            return self.site_count_with_filter()
        else:
            self.cur.execute(u"SELECT COUNT(*) FROM \'{0:s}\';".format(self.encoded_tab,))
            self.db.commit()
            result = self.cur.fetchone()
            return result[0]

    def update_sites(self, sites: []):
        pass

    def delete_sites(self, sites: []):
        if len(sites) < 1:
            return
        need_to_delete = []
        try:
            for item in sites:
                if isinstance(item, str):
                    need_to_delete.append(item)
                elif hasattr(item, "domain"):
                    need_to_delete.append(item.domain)
            self.cur.executemany(u"DELETE FROM \'{0:s}\' WHERE DOMAIN=?;".format(self.encoded_tab, ), need_to_delete)
            self.db.commit()
        except Exception as ex:
            msg = "delete_sites() " + self.tab
            ErrorLogger.log_error(self.db_type, ex, msg)

    def close(self):
        self.db.close()


class SeedSiteDB(DBInterface):
    def __init__(self, table: str, offset=0, db_addr: str=None, db_filter=SeedSiteFilter()):
        memTest = "CREATE TABLE IF NOT EXISTS \'%s\'(DOMAIN TEXT, PAGE_C INTEGER, PRIMARY KEY(DOMAIN));" % (table,)
        DBInterface.__init__(self, table=table, creation_query=memTest, db_addr=db_addr, offset=offset,
                             databaseType=SiteSource.Seed, db_filter=db_filter)
        self.db_filter = db_filter

    @staticmethod
    def get_fields_names():
        return "DOMAIN", "PAGE_C"

    def add_sites(self, sites, skip_check=False):
        if len(sites) < 1:
            return
        if skip_check:
            need_to_add = sites
        else:
            need_to_add = []
        try:
            if not skip_check:
                for item in sites:
                    if isinstance(item, str):
                        # cur = self.cur.execute("SELECT EXISTS(SELECT 1 FROM \'{0:s}\' WHERE DOMAIN=\'{1:s}\' LIMIT 1);"
                        #                        .format(self.tab, item,))
                        # result = cur.fetchone()
                        # if result[0] == 0:
                        need_to_add.append((item, 0))
                    elif isinstance(item, SeedSiteFeedback):
                        # cur = self.cur.execute("SELECT EXISTS(SELECT 1 FROM \'{0:s}\' WHERE DOMAIN=\'{1:s}\' LIMIT 1);"
                        #                        .format(self.tab, item.domain,))
                        # result = cur.fetchone()
                        # if result[0] == 0:
                        need_to_add.append((item.domain, item.page_count))

            self.cur.executemany(u"INSERT OR IGNORE INTO \'{0:s}\' (DOMAIN, PAGE_C) VALUES (?, ?);".format(self.encoded_tab, ), need_to_add)
            self.db.commit()
        except Exception as ex:
            print(ex)
            msg = "add_sites() " + self.tab
            ErrorLogger.log_error("SeedSiteDB", ex, msg)
        return need_to_add

    def import_from_file(self, file_path: str):
        if file_path.endswith(".csv"):
            with open(file_path, newline="") as csv_file:
                reader = csv.reader(csv_file, delimiter=',')
                self.add_sites([(x[0], 0) for x in reader], True)
        else:
            raise ValueError("other format is not supported.")

    def site_count_with_filter(self):
        self.cur.execute(u"SELECT COUNT(*) FROM \'{0:s}\' WHERE PAGE_C>={1:d};".format(self.encoded_tab, self.db_filter.min_page))
        result = self.cur.fetchone()
        return result[0]

    def update_sites(self, sites: []):
        if sites is not None and len(sites) > 0:
            need_to_update = []
            for site in sites:  # SeedSiteFeedback
                need_to_update.append((site.page_count, site.domain))
                #if isinstance(site, SeedSiteFeedback):
            try:
                self.cur.executemany(u"UPDATE \'{0:s}\' SET PAGE_C=? WHERE DOMAIN=?;".format(self.encoded_tab), need_to_update)
                self.db.commit()
            except Exception as ex:
                ErrorLogger.log_error("SeedSiteDB", ex, "update_sites")
            # for site in sites:
            #     #if isinstance(site, SeedSiteFeedback):
            #     self.cur.execute(u"UPDATE \'{0:s}\' SET PAGE_C={1:d} WHERE DOMAIN=\'{2:s}\';"
            #                      .format(self.tab, site.page_count, site.domain))
            # self.db.commit()

    def get_next_patch(self, count: int, rollover=True, **kwargs) ->[]:  # if you need a custom filtered implmentation
        with self.get_lock:
            page_count = 0
            if self.db_filter is not None:
                page_count = self.db_filter.min_page
            if page_count == 0:
                return [x[0] for x in super(SeedSiteDB, self).get_next_patch(count=count, rollover=rollover, **kwargs)]
            else:
                result = []
                total = self.site_count(False)
                if total > 0:
                    q = u"SELECT DOMAIN, rowid FROM \'{0:s}\' WHERE PAGE_C >={1:d} " \
                        u"ORDER BY rowid LIMIT {2:d} OFFSET {3:d};".format(self.encoded_tab, page_count, count, self.offset)
                    #print(q)
                    cur = self.cur.execute(q)
                    temp = cur.fetchall()
                    results_count = len(temp)
                    if results_count > 0:
                        for domain, rowid in temp:
                            result.append(domain)
                        self.offset += results_count
                    if rollover and results_count < count:
                        self.offset = 0
                        result += self.get_next_patch(count - results_count, False, **kwargs)
                return result

    def get_next_patch_v1(self, count: int, rollover=True, **kwargs) ->[]:  # if you need a custom filtered implmentation
        page_count = 0
        if self.db_filter is not None:
            page_count = self.db_filter.min_page
        if page_count == 0:
            return [x[0] for x in super(SeedSiteDB, self).get_next_patch(count=count, rollover=rollover, **kwargs)]
        else:
            result = []
            total = self.site_count(False)

            if self.offset < total:
                innerCount = 0
                while not (innerCount > total or len(result) >= count):
                    if not rollover and self.offset > total:
                        break
                    cur = self.cur.execute(
                        u"SELECT DOMAIN, PAGE_C FROM \'{0:s}\' ORDER BY rowid LIMIT {1:d} OFFSET {2:d};"
                        .format(self.encoded_tab, 1, self.offset))
                    temp = cur.fetchone()
                    domain = ""
                    page = 0
                    try:
                        domain = temp[0]
                        page = temp[1]
                        if page is None:
                            page = 0
                    except:
                        pass
                    if page >= page_count:
                        result.append(domain)
                    innerCount += 1
                    self.offset += 1
                    if self.offset > total and rollover:
                        self.offset = 0

            return result


class FilteredResultDB(DBInterface):
    def __init__(self, table: str, offset=0, db_addr: str=None, bad_db=False, db_filter=FilteredResultFilter()):
        memTest = "CREATE TABLE IF NOT EXISTS \'%s\'(DOMAIN TEXT, TF INTEGER, CF INTEGER, DA INTEGER, ARCHIVE INTEGER, " \
                  "FOUND INTEGER,PRICE REAL, REF_DOMAINS INTEGER, DOMAIN_VAR TEXT, BACKLINKS INTEGER, TOPIC TEXT, EXCEPTION TEXT," \
                  "PRIMARY KEY(DOMAIN));" % (table,)
        if not bad_db:
            DBInterface.__init__(self, table=table, creation_query=memTest, db_addr=db_addr, offset=offset,
                                 databaseType=SiteSource.Flitered, db_filter=db_filter)
        else:  # database contains bad results.
            DBInterface.__init__(self, table=table, creation_query=memTest, db_addr=db_addr, offset=offset,
                     databaseType=SiteSource.Filtered_bad, db_filter=db_filter)
        self.db_filter = db_filter

    @staticmethod
    def get_fields_names():
        return "DOMAIN", "TF", "CF", "DA", "ARCHIVE", "FOUND", "PRICE", "REF DOMAINS", "DOMAIN VAR", "BACKLINKS", "TOPIC", "EXCEPTION"

    def get_all_sites(self) ->[]:
        self.cur.execute("SELECT * FROM \'%s\';" % (self.encoded_tab,))
        self.db.commit()
        return self.cur.fetchall()

    def add_sites(self, sites, skip_check=False):
        if len(sites) < 1:
            return
        need_to_add = []
        if not skip_check:
            for item in sites:
                if isinstance(item, FilteredDomainData):
                    need_to_add.append((item.domain, item.tf, item.cf, item.da,
                                        item.archive, item.found, item.price,
                                        item.ref_domains, item.domain_var, item.backlinks, item.topic,item.exception))
        else:
            need_to_add = sites

        try:
            self.cur.executemany(u"INSERT OR REPLACE INTO \'{0:s}\' (DOMAIN, TF, CF, DA, ARCHIVE, FOUND, PRICE, "
                                 u"REF_DOMAINS, DOMAIN_VAR, BACKLINKS, TOPIC, EXCEPTION) VALUES"
                                 u" (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);".format(self.encoded_tab,), need_to_add)
            self.db.commit()
        except Exception as ex:
            ErrorLogger.log_error("FilteredResultDB", ex, "add_sites()")

        return need_to_add

    def site_count_with_filter(self):
        self.cur.execute(u"SELECT COUNT(*) FROM \'{0:s}\' WHERE TF >={1:d}  AND CF >={2:d} AND DA >={3:d} "
                         u"AND ARCHIVE >={4:d} AND REF_DOMAINS >={5:d} AND BACKLINKS >= {6:d};"
                         .format(self.encoded_tab, self.db_filter.tf, self.db_filter.cf, self.db_filter.da, self.db_filter.arc,
                                 self.db_filter.ref_domains, self.db_filter.backlinks))
        result = self.cur.fetchone()
        return result[0]


class ExternalSiteDB(DBInterface):
    def __init__(self, table: str, offset=0, db_addr: str=None, db_filter=ExternalSiteDBFilter()):
        memTest = "CREATE TABLE IF NOT EXISTS \'%s\'(DOMAIN TEXT, CODE INTEGER, PRIMARY KEY(DOMAIN));" % (table,)
        DBInterface.__init__(self, table=table, creation_query=memTest, db_addr=db_addr, offset=offset,
                             databaseType=SiteSource.AllExternal, db_filter=db_filter)
        self.db_filter = db_filter

    @staticmethod
    def get_fields_names():
        return "DOMAIN", "CODE"

    def add_sites(self, sites: [], skip_check=False):
        if len(sites) < 1:
            return

        need_to_add = []
        if not skip_check:
            for item in sites:  # item type is ScrapeDomainData
                ext = tldextract.extract(item.domain)
                root = ext.domain+"."+ext.suffix
                item.domain = root
                #if ext.suffix in CommonTLD.Frequent_tlds:
                # cur = self.cur.execute("SELECT EXISTS(SELECT 1 FROM \'{0:s}\' WHERE DOMAIN=\'{1:s}\' LIMIT 1);"
                #                        .format(self.tab, item.domain,))
                # result = cur.fetchone()
                # if result[0] == 0:
                need_to_add.append((item.domain, item.code))
        else:
            need_to_add = sites

        try:
            self.cur.executemany(u"INSERT OR IGNORE INTO \'{0:s}\' (DOMAIN, CODE) VALUES (?, ?);".format(self.encoded_tab,), need_to_add)
            self.db.commit()
        except Exception as ex:
            ErrorLogger.log_error("ExternalSiteDB", ex, "add_sites()")
        return need_to_add

    def update_sites(self, sites: []):
        if sites is not None and len(sites) > 0:
            need_to_update = []
            for site in sites:
                need_to_update.append((site.code, site.domain))
                #if isinstance(site, ScrapeDomainData):
            self.cur.executemany(u"UPDATE \'{0:s}\' SET CODE=? WHERE DOMAIN=?;".format(self.encoded_tab,), need_to_update)
            self.db.commit()

    def get_next_patch(self, count: int, rollover=True, equal=True, **kwargs):
        """
        :param count:
        :param rollover:
        :param equal: if equal, then it will looking for code == target code, else looking for code != target code
        :param kwargs:
        :return:
        """
        fil = self.db_filter
        if fil is None or not fil.need_filtering():
            data = super(ExternalSiteDB, self).get_next_patch(count=count, rollover=rollover, **kwargs)
            if self.output_format_tuple:
                return [ScrapeDomainData(x[0], x[1]) for x in data]
            else:
                return data
        else:
            result = []
            total = self.site_count(False)

            if total > 0:
                cur = self.cur.execute(
                    u"SELECT DOMAIN, CODE, rowid FROM \'{0:s}\' WHERE CODE{1:s}{2:d} "
                    u"ORDER BY rowid LIMIT {3:d} OFFSET {4:d};"
                    .format(self.encoded_tab, fil.sign, fil.code, count, self.offset))
                temp = cur.fetchall()
                results_count = len(temp)
                if results_count > 0:
                    for domain, code, rowid in temp:
                        if not self.output_format_tuple:
                            result.append(ScrapeDomainData(domain, code))
                        else:
                            result.append((domain, code))
                        self.offset += results_count
                if rollover and results_count < count:
                    self.offset = 0
                    result += self.get_next_patch(count - results_count, False, **kwargs)
            return result

    def get_next_patch_v1(self, count: int, rollover=True, equal=True, **kwargs):
        """
        :param count:
        :param rollover:
        :param equal: if equal, then it will looking for code == target code, else looking for code != target code
        :param kwargs:
        :return:
        """
        fil = self.db_filter
        if fil is None or not fil.need_filtering():
            return [ScrapeDomainData(x[0], x[1]) for x in super(ExternalSiteDB, self).get_next_patch(count=count, rollover=rollover, **kwargs)]
        else:
            result = []
            total = self.site_count(False)

            if self.offset < total:
                innerCount = 0
                while not (innerCount > total or len(result) >= count):
                    if not rollover and self.offset > total:
                        break
                    cur = self.cur.execute(
                        u"SELECT DOMAIN, CODE FROM \'{0:s}\' ORDER BY rowid LIMIT {1:d} OFFSET {2:d};"
                        .format(self.encoded_tab, 1, self.offset))
                    temp = cur.fetchone()
                    domain = ""
                    code = 0
                    try:
                        domain = temp[0]
                        code = temp[1]
                        if code is None:
                            code = 0
                    except:
                        pass
                    if equal and code == fil.code:
                        result.append(ScrapeDomainData(domain, code))
                    elif not equal and code != fil.code:
                        result.append(ScrapeDomainData(domain, code))
                    innerCount += 1
                    self.offset += 1
                    if self.offset > total and rollover:
                        self.offset = 0

            return result

    def site_count_with_filter(self):
        self.cur.execute(u"SELECT COUNT(*) FROM \'{0:s}\' WHERE CODE=={1:d};".format(self.encoded_tab, self.db_filter.code))
        result = self.cur.fetchone()
        return result[0]


