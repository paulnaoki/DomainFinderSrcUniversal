from DomainFinderSrc.Utilities.Serializable import Serializable


class FilteredDomainData(Serializable):
    def __init__(self, domain: str="", tf: int=0, cf: int=0, da: int=0,
                 ref_domains: int=0, domain_var: str="", backlinks: int=0, topic: str="",
                 price: float=0, archive: int=0, found: int=0, tf_cf_deviation=0):
        self.domain = domain
        self.tf = tf
        self.cf = cf
        self.da = da
        self.ref_domains = ref_domains
        self.domain_var = domain_var
        self.backlinks = backlinks
        self.topic = topic
        self.price = price
        self.archive = archive
        self.found = found
        self.tf_cf_deviation = tf_cf_deviation
        self.exception = ""

    def to_tuple(self):
        return (self.domain, self.tf, self.cf, self.da, self.ref_domains, self.domain_var, self.backlinks, self.topic,
                self.price, self.archive, self.found, self.tf_cf_deviation, self.exception)

    @staticmethod
    def from_tuple(data: tuple):
        # "DOMAIN", "TF", "CF", "DA", "ARCHIVE", "FOUND", "PRICE", "REF DOMAINS", "DOMAIN VAR", "BACKLINKS", "TOPIC", "EXCEPTION"
        item = FilteredDomainData()
        if len(data) == 13:
            item.domain, item.tf, item.cf, item.da, item.ref_domains, item.domain_var, item.backlinks, item.topic,\
            item.price, item.archive, item.found, item.tf_cf_deviation, item.exception = data
        elif len(data) == 12:
            item.domain, item.tf, item.cf, item.da, \
            item.archive, item.found, item.price, item.ref_domains, \
            item.domain_var, item.backlinks, item.topic, item.exception = data
        elif len(data) == 11:
            item.domain, item.tf, item.cf, item.da, \
            item.archive, item.found, item.price, item.ref_domains, \
            item.domain_var, item.backlinks, item.topic = data
        return item

    def __str__(self):
        return str(self.__dict__)


class ScrapeDomainData(Serializable):
    def __init__(self, domain: str="", code: int=0):
        self.domain = domain
        self.code = code

    def to_tuple(self):
        return (self.domain, self.code)

    def __str__(self):
        return self.domain + " " + str(self.code)