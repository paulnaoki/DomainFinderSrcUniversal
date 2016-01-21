from DomainFinderSrc.MiniServer.Common.DBInterface import DBInterface, DBType, FilteredDomainData
from DomainFinderSrc.Utilities.Serializable import Serializable
from DomainFinderSrc.Utilities.StrUtility import StrUtility
from DomainFinderSrc.MajesticCom.Category import CategoryManager
# result site db


class CatagoryDomainSiteDataStruct(Serializable):

    def __init__(self, domain: str="", domain_var: str="", tf: int=0, cf: int=0, da: int=0, ref_domains: int=0,
                 backlinks: int="", price: float=0.0, rate: float=0.0, tf_cf_ratio: float=0.0,
                 topic1: str="", topic1_s: int=0, topic2: str="", topic2_s: int=0, topic3: str="", topic3_s: int=0,
                 archive_count: int=0, best_archive: str="", found: int=0, note: str="", domain_id: str=""):
        self.domain, self.domain_var = domain, domain_var
        self.tf, self.cf, self.da = tf, cf, da
        self.ref_domains, self.backlinks, self.price, self.rate, self.tf_cf_devi = ref_domains, backlinks, price, rate, tf_cf_ratio
        self.topic1, self.topic1_s, self.topic2, self.topic2_s, self.topic3, self.topic3_s = topic1, topic1_s, topic2, topic2_s, topic3, topic3_s
        self.arhive_count, self.best_archive, self.found, self.note, self.domain_id = archive_count, best_archive, found, note, domain_id

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
            self.rate, self.tf_cf_devi, self.topic1, self.topic1_s, self.topic2, self.topic2_s, self.topic3, self.topic3_s, \
            self.arhive_count, self.best_archive, self.found, self.note, self.domain_id

    def __str__(self):
        return str(self.__dict__)

    @staticmethod
    def from_tuple(obj: tuple):
        domain, domain_var, tf, cf, da, ref_domains, backlinks, price, rate, tf_cf_ratio, topic1, topic1_s, topic2, topic2_s, topic3, topic3_s, archive_count, best_archive, found, note, domain_id = obj

        return CatagoryDomainSiteDataStruct(domain, domain_var, tf, cf, da, ref_domains, backlinks, price,
               rate, tf_cf_ratio, topic1, topic1_s, topic2, topic2_s, topic3, topic3_s,
               archive_count, best_archive, found, note, domain_id)

    @staticmethod
    def from_FilteredDomainData(data: FilteredDomainData):
        obj = CatagoryDomainSiteDataStruct()
        obj.domain, obj.domain_var = data.domain, data.domain_var
        obj.tf, obj.cf, obj.da, obj.backlinks, obj.arhive_count, obj.ref_domains = data.tf, data.cf, data.da, \
                                                                                   data.backlinks, data.archive,\
                                                                                   data.ref_domains
        obj.price, obj.found = data.price, data.found
        if data.cf > 0:
            obj.tf_cf_devi = abs(1 - data.tf/data.cf)
        else:
            obj.tf_cf_devi = 100.0

        splited_topics = data.topic.split(";")
        counter = 0
        for item in splited_topics:
            counter += 1
            if len(item) == 0:
                continue
            topic, trust_flow = item.split(":")
            if len(topic) == 0 or len(trust_flow) == 0:
                continue
            else:
                parsed_catagory = str(CategoryManager.decode_sub_category(topic, False))
                score = int(trust_flow)
                formated_ca = "topic{0:d}".format(counter, )
                formated_s = "topic{0:d}_s".format(counter,)
                if hasattr(obj, formated_ca):
                    setattr(obj, formated_ca, parsed_catagory)
                    setattr(obj, formated_s, score)

        return obj

    @staticmethod
    def get_tuple_len():
        return 21


class CategoryDomainSiteDB(DBInterface):

    def __init__(self, db_path: str):
        table_name = "CategoryDomain"
        creation_query = u"CREATE TABLE IF NOT EXISTS \'{0:s}\'" \
                         u"(DOMAIN TEXT, DOMAIN_VAR TEXT, TF INTEGER, CF INTEGER, DA INTEGER, REF_DOMAINS INTEGER, BACKLINK INTEGER," \
                         u"PRICE FLOAT, RATE FLOAT, TF_CF_RATIO FLOAT, TOPIC1 TEXT, TOPIC1_S INTEGER, TOPIC2 TEXT, TOPIC2_S INTEGER, TOPIC3 TEXT, TOPIC3_S INTEGER," \
                         u"ARCHIVE_COUNT INTEGER, BEST_ARCHIVE TEXT, FOUND INTEGER, NOTE TEXT, UID TEXT," \
                         u" PRIMARY KEY(DOMAIN));".format(table_name,)
        insert_query = u"INSERT OR REPLACE INTO \'{0:s}\' (DOMAIN, DOMAIN_VAR, TF, CF, DA, REF_DOMAINS, BACKLINK, " \
                       u"PRICE, RATE, TF_CF_RATIO, TOPIC1, TOPIC1_S, TOPIC2, TOPIC2_S, TOPIC3, TOPIC3_S, ARCHIVE_COUNT, " \
                       u"BEST_ARCHIVE, FOUND, NOTE, UID) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?," \
                       u"?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"
        DBInterface.__init__(self, table=table_name, db_addr=db_path,
                             creation_query=creation_query, insert_query=insert_query, databaseType=DBType.Type_Marketplace)

    @staticmethod
    def get_fields_names():
        return "DOMAIN", "DOMAIN_VAR", "TF", "CF", "DA", "REF_DOMAINS", "BACKLINK", \
               "PRICE", "RATE", "TF_CF_RATIO", "TOPIC1", "TOPIC1_S", "TOPIC2", "TOPIC2_S", "TOPIC3", "TOPIC3_S", "ARCHIVE_COUNT",\
               "BEST_ARCHIVE", "FOUND", "NOTE", "UID"

    @staticmethod
    def get_query_para(**para) -> dict:
        raise NotImplementedError

    def convert_query_para(self, **kwargs) -> str:
        full_query = ""
        if len(kwargs) > 0:
            domain, uid, topic1, topic2, topic3 = map(lambda x: kwargs.get(x, ""), ["DOMAIN", "UID",
                                                                                    "TOPIC1", "TOPIC2", "TOPIC3"])
            tf, cf, da, ref_domain, backlinks, topic1_s, topic2_s, topic3_s, archive_c, found = \
                map(lambda x: kwargs.get(x, 0), ["TF", "CF", "DA", "REF_DOMAINS", "BACKLINK",
                                                 "TOPIC1_S", "TOPIC2_S", "TOPIC3_S", "ARCHIVE_COUNT", "FOUND"])
            # price, rate, tf_cf_ratio = map(lambda x: kwargs.get(x, 0.0), ["PRICE", "RATE", "TF_CF_RATIO"])
            queries = []
            if len(domain) > 0:
                queries.append("DOMAIN = " + domain)
            if len(uid) > 0:
                queries.append("UID = " + uid)
            non_empty_topics = [x for x in filter(lambda x: len(x) > 0, [topic1, topic2, topic3])]
            if len(non_empty_topics) > 0:
                topics = ", ".join(map(lambda x: "\'{0:s}\'".format(x,), non_empty_topics))
                topic_format = "(TOPIC{2:d} IN ({0:s}) AND TOPIC{2:d}_S >= {1:d})"
                topic_query = "("+" OR ".join(map(lambda x: topic_format.format(topics, topic1_s, x,), range(1, 4)))+")"
                queries.append(topic_query)
            if tf > 0:
                queries.append("TF >= "+str(tf))
            if cf > 0:
                queries.append("CF >= "+str(cf))
            if da > 0:
                queries.append("DA >= "+str(da))
            if len(queries) > 0:
                full_query += "WHERE " + " AND ".join(queries)
                    
                # query += ("" if count == 0 else " AND "
        return full_query

    def convert_input(self, obj):
        if isinstance(obj, CatagoryDomainSiteDataStruct):
            return obj.to_tuple()
        elif isinstance(obj, tuple) and len(obj) == CatagoryDomainSiteDataStruct.get_tuple_len():
            return obj
        else:
            raise TypeError()

    def convert_output(self, obj):
        return CatagoryDomainSiteDataStruct.from_tuple(obj)
