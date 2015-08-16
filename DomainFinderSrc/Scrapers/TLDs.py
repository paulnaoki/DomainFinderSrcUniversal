import tldextract


class TldUtility:

    SUPPORT_TLD_LIST = [  # tld you can buy
        "com", "org", "co.uk", "info", "biz", "net", "edu", "mobi",
        "uk", "ca", "de", "fr", "us", "ch", "it", "nl", "se", "es",
        "be", "dk", "pl", "in", "eu", "co", "com.au", "net.au", "org.au", "net.nz",
        "tv", "io", "cc", "xxx"
    ]

    TOP_TLD_LIST = [  # tld mostly in enlgish
        "com", "org", "info", "biz", "net", "mobi", "io", "co", "cc", "eu",
        "us", "ca", "com.au", "net.au", "org.au", "net.nz", "co.nz",
    ]

    @staticmethod
    def is_supported_tld(domain: str):
        info = tldextract.extract(domain)
        suffix = info.suffix
        if suffix in TldUtility.SUPPORT_TLD_LIST:
            return True
        else:
            return False

    @staticmethod
    def is_top_tld(domain: str):
        info = tldextract.extract(domain)
        suffix = info.suffix
        if suffix in TldUtility.TOP_TLD_LIST:
            return True
        else:
            return False
