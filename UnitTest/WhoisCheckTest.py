# from DomainFinderSrc.Scrapers.ExternalSiteChecker import WhoisChecker, WhoisCheckerState
from DomainFinderSrc.Scrapers.SiteTempDataSrc.SiteTempDataSrcInterface import OnSiteLink, ResponseCode
from unittest import TestCase
from DomainFinderSrc.Scrapers.TLDs import TldUtility
from DomainFinderSrc.Scrapers.LinkChecker import LinkChecker


def check_whois(domain_data: OnSiteLink):
    root_domain = domain_data.link.lower()
    try:
        if root_domain.startswith("http"):
            root_domain = LinkChecker.get_root_domain(domain_data.link)[1]
        is_available, is_redemption = LinkChecker.is_domain_available_whois(root_domain)  # check whois record
        if is_available or is_redemption:
            if is_available:
                real_response_code = ResponseCode.Expired
            else:
                real_response_code = ResponseCode.MightBeExpired
            domain_data.link = root_domain
            domain_data.response_code = real_response_code
            #return_obj = OnSiteLink(root_domain, real_response_code, domain_data.link_level, OnSiteLink.TypeOutbound)
            # self._output_q.put((domain_data.link, domain_data.response_code))
    except Exception as ex:
        print(ex)
    finally:
        return domain_data.link, domain_data.response_code


def check_whois_with_dns(page: OnSiteLink):

    real_response_code = ResponseCode.DNSError
    skip_whois_check = False
    try:
        root_result = LinkChecker.get_root_domain(page.link)
        root_domain = root_result[1]
        sub_domain = root_result[4]
        suffix = root_result[5]

        if len(sub_domain) == 0 or suffix not in TldUtility.TOP_TLD_LIST:
            skip_whois_check = True
        else:

            if LinkChecker.is_domain_DNS_OK(sub_domain):  # check DNS first
                real_response_code = ResponseCode.NoDNSError
                skip_whois_check = True
            elif not sub_domain.startswith("www."):
                if LinkChecker.is_domain_DNS_OK("www." + root_domain):
                    real_response_code = ResponseCode.NoDNSError
                    skip_whois_check = True
                # response = LinkChecker.get_response(page.link, timeout)  # check 404 error

            page.response_code = real_response_code
            page.link_type = OnSiteLink.TypeOutbound
            page.link = root_domain

    except Exception as ex:
        # ErrorLogger.log_error("WhoisChecker", ex, "_check_whois_with_dns() " + page.link)
        skip_whois_check = True
    finally:
        if not skip_whois_check and real_response_code == ResponseCode.DNSError:
            return check_whois(page)
        else:
            return page.link, page.response_code


class WhoisCheckTest(TestCase):
    def testWhoisDNS(self):
        test_domains = ['abacouncensored.com', 'sexy-chat-rooms.org', 'girlxxxfree.info', 'yourptr.us',
                        'nick-rees-enterprises.net', 'unibag.co.nz']
        for item in [OnSiteLink(link=x, response_code=ResponseCode.DNSError) for x in test_domains]:
            print(check_whois_with_dns(item))


if __name__ == "__main__":
    test = WhoisCheckTest()
    test.testWhoisDNS()