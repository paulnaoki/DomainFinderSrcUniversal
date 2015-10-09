class MajesticComStruct:
    def __init__(self, domain="", tf: int=0, cf: int=0, ref_domains: int=0, backlinks: int=0, topic: str=0):
        self.domain = domain
        self.tf = tf
        self.cf = cf
        self.ref_domains = ref_domains
        self.backlinks = backlinks
        self.topic = topic

    def __str__(self):
        return self.domain + " tf:" + str(self.tf) + " cf:" + str(self.cf) + " topic:" + self.topic


class MajesticRefDomainStruct:
    def __init__(self, domain="", tf: int=0, cf: int=0, country: str="",
                 backlinks: int=0, ref_domains: int=0, ip: str="", alexa_rank: int=0):
        self.domain = domain
        self.tf = tf
        self.cf = cf
        self.country = country
        self.backlinks = backlinks
        self.ref_domains = ref_domains
        self.ip = ip
        self.alexa_rank = alexa_rank

    def __str__(self):
        return self.domain + " tf:" + str(self.tf) + " cf:" + str(self.cf) + " alexa:" + str(self.alexa_rank) + \
            " country:" + self.country


class MajesticBacklinkDataStruct:
    def __init__(self, ref_domain="", backlink="", src_tf: int=0, src_cf: int=0, src_topic="", src_topical_tf=0):
        self.ref_domain = ref_domain
        self.backlink = backlink
        self.src_tf = src_tf
        self.src_cf = src_cf
        self.src_topic = src_topic
        self.src_topic_tf = src_topical_tf

    def __str__(self):
        return self.ref_domain + " tf:" + str(self.src_tf) + " cf:" + str(self.src_cf) + " backlink:" + self.backlink \
            + " topic:" + self.src_topic + " topic tf:" + str(self.src_topic_tf)

    @staticmethod
    def get_tilte():
        return "REF DOMAIN", "BACKLINK", "SRC TF", "SRC CF", "SRC TOPIC", "SRC TOPIC TF"

    def to_tuple(self):
        return self.ref_domain, self.backlink, self.src_tf, self.src_cf, self.src_topic, self.src_topic_tf