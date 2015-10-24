from DomainFinderSrc.MiniServer.Common.DBInterface import DBInterface, DBType
from DomainFinderSrc.Utilities.Serializable import Serializable

# result site db


class CatagoryDomainSiteDataStruct(Serializable):

    def __init__(self, domain: str="", domain_var: str="", tf: int=0, cf: int=0, da: int=0, ref_domains: int=0,
                 backlinks: int="", price: float=0.0, rate: float=0.0, tf_cf_ratio: float=0.0,
                 topic1: str="", topic1_s: int=0, topic2: str="", topic2_s: int=0, topic3: str="", topic3_s: int=0,
                 archive_count: int=0, best_archive: str="", found: int=0, note: str=""):
        self.domain, self.domain_var = domain, domain_var
        self.tf, self.cf, self.da = tf, cf, da
        self.ref_domains, self.backlinks, self.price, self.rate, self.tf_cf_ratio = ref_domains, backlinks, price, rate, tf_cf_ratio
        self.topic1, self.topic1_s, self.topic2, self.topic2_s, self.topic3, self.topic3_s = topic1, topic1_s, topic2, topic2_s, topic3, topic3_s
        self.arhive_count, self.best_archive, self.found, self.note = archive_count, best_archive, found, note

    def get_categories(self) ->[]:
        topics = []
        if len(self.topic1) > 0:
            topics.append(self.topic1)
        if len(self.topic2) > 0:
            topics.append(self.topic2)
        if len(self.topic3) > 0:
            topics.append(self.topic3)
        return topics

    def to_tuple(self):
        return self.domain, self.domain_var, self.tf, self.cf, self.da, self.ref_domains, self.backlinks, self.price, \
            self.rate, self.tf_cf_ratio, self.topic1, self.topic1_s, self.topic2, self.topic2_s, self.topic3, self.topic3_s, \
            self.arhive_count, self.best_archive, self.found, self.note

    def __str__(self):
        return str(self.__dict__)

    @staticmethod
    def from_tuple(obj: tuple):
        domain, domain_var, tf, cf, da, ref_domains, backlinks, price, \
        rate, tf_cf_ratio, topic1, topic1_s, topic2, topic2_s, topic3, topic3_s, \
        archive_count, best_archive, sfound, note = obj

        return CatagoryDomainSiteDataStruct(domain, domain_var, tf, cf, da, ref_domains, backlinks, price,
               rate, tf_cf_ratio, topic1, topic1_s, topic2, topic2_s, topic3, topic3_s,
               archive_count, best_archive, sfound, note)

    @staticmethod
    def get_tuple_len():
        return 20


class CategoryDomainSiteDB(DBInterface):

    def __init__(self, db_path: str):
        table_name = "CategoryDomain"
        creation_query = u"CREATE TABLE IF NOT EXISTS \'{0:s}\'" \
                         u"(DOMAIN TEXT, DOMAIN_VAR TEXT, TF INTEGER, CF INTEGER, DA INTEGER, REF_DOMAINS INTEGER, BACKLINK INTEGER," \
                         u"PRICE FLOAT, RATE FLOAT, TF_CF_RATIO FLOAT, TOPIC1 TEXT, TOPIC1_S INTEGER, TOPIC2 TEXT, TOPIC2_S INTEGER, TOPIC3 TEXT, TOPIC3_S INTEGER," \
                         u"ARCHIVE_COUNT INTEGER, BEST_ARCHIVE TEXT, FOUND INTEGER, NOTE TEXT," \
                         u" PRIMARY KEY(DOMAIN));".format(table_name,)
        insert_query = u"INSERT OR REPLACE INTO \'{0:s}\' (DOMAIN, DOMAIN_VAR, TF, CF, DA, REF_DOMAINS, BACKLINK, " \
                       u"PRICE, RATE, TF_CF_RATIO, TOPIC1, TOPIC1_S, TOPIC2, TOPIC2_S, TOPIC3, TOPIC3_S, ARCHIVE_COUNT, " \
                       u"BEST_ARCHIVE, FOUND, NOTE) VALUES (?, ?, ?, ?, ?, ?, ?, ?, " \
                       u"?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"
        DBInterface.__init__(self, table=table_name, db_addr=db_path,
                             creation_query=creation_query, insert_query=insert_query, databaseType=DBType.Type_Marketplace)

    @staticmethod
    def get_fields_names():
        return "DOMAIN", "DOMAIN_VAR", "TF", "CF", "DA", "REF_DOMAINS", "BACKLINK", \
               "PRICE", "RATE", "TF_CF_RATIO", "TOPIC1", "TOPIC1_S", "TOPIC2", "TOPIC2_S", "TOPIC3", "TOPIC3_S", "ARCHIVE_COUNT",\
               "BEST_ARCHIVE", "FOUND", "NOTE"

    def convert_query_para(self, **kwargs) -> str:
        return ""

    def convert_input(self, obj):
        if isinstance(obj, CatagoryDomainSiteDataStruct):
            return obj.to_tuple()
        elif isinstance(obj, tuple) and len(obj) == CatagoryDomainSiteDataStruct.get_tuple_len():
            return obj
        else:
            raise TypeError()

    def convert_output(self, obj):
        return CatagoryDomainSiteDataStruct.from_tuple(obj)
