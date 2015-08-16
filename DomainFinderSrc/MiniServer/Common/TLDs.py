import tldextract


class CommonTLD:
    tld_com = "com"
    tld_net = "net"
    tld_org = "org"
    tld_info = "info"
    tld_ca = "ca"
    tld_us = "us"
    tld_eu = "eu"
    tld_biz = "biz"
    tld_tv = "tv"
    tld_me = "me"
    tld_de = "de"
    tld_cc = "cc"
    tld_name = "name"
    tld_ws = "ws"
    tld_mobi = "mobi"
    tld_fm = "fm"
    tld_am = "am"
    tld_es = "es"
    tld_asia = "asia"
    tld_se = "se"
    tld_xxx = "xxx"
    tld_it = "it"
    tld_co_uk = "co.uk"
    tld_cn = "cn"
    tld_jp = "jp"

    Frequent_tlds = [tld_com, tld_co_uk, tld_org, tld_net]

    @staticmethod
    def is_target_in_list(domain: str, common_list: []):
        if domain is not None and common_list is not None:
            suffix = tldextract.extract(domain).suffix
            if suffix in common_list:
                return True
            else:
                return False
        else:
            return False

    @staticmethod
    def get_frequent_tlds()->[]:
        return CommonTLD.Frequent_tlds