from unittest import TestCase
from DomainFinderSrc.MajesticCom import *
from DomainFinderSrc.SiteConst import *
import re
account = SiteAccount(siteType=AccountType.Majestic, userID="will@bazookasearch.com", password="baltimore9!",
                      APIkey="1BB1D141D20CAF35D331F086F55C1CEE")
majestic = MajesticCom(account)


class MajesticTest(TestCase):

    def testTF_CF(self):
        data = majestic.get_cf_tf_list(["www.articleroller.com", "http://www.articleroller.com"], True)
        for item in data:
            print(item)

    def test_anchor_text(self):
        data = majestic.get_anchor_text_info(domain="susodigital.com", is_dev=False)
        print(data)
        print("number of data points: ", len(data[0]))

    def test_ref_domains(self):
        data = majestic.get_ref_domains(domain="susodigital.com", is_dev=False)
        for item in data:
            print(item)

    def testWesternLan(self):
        def is_valid_ISO8859_1_str(original_str: str) -> bool:
            try:
                temp = original_str.encode(encoding='iso-8859-1').decode(encoding='iso-8859-1')
                if temp == original_str:
                    return True
                else:
                    return False
            except:
                return False

        strs = ["travel log", "something", "中国字", "Агент Mail.Ru", "conférence des communautés homosexuelle"]
        for original_str in strs:
            print(original_str, " is valid?:", is_valid_ISO8859_1_str(original_str))

    def testAnchorText(self):
        self._spam_anchor = ["tit", "sex", "oral sex", "熟女"]

        def isOK(domain: str):
            min_anchor_variation_limit = 2
            no_follow_limit = 0.5
            domain_contain_limit = 5
            is_in_anchor = False
            temp_list = ["boot", "tistd", "bbc.co.uk", "ok", "美熟女", "中国", "afafa", "fafa"]
            #temp_list = ["boot", "tistd", "ok", "中国", "熟女s", "bbc.co.uk"]
            anchor_list, total, deleted, nofollow = (temp_list, 1000, 200, 100)  # change this
            if len(anchor_list) <= min_anchor_variation_limit:
                raise ValueError("number of anchor variation is less than 2.")
            elif (deleted + nofollow)/total > no_follow_limit:
                raise ValueError("deleted and nofollow backlinks are more than 50%.")
            elif len(self._spam_anchor) > 0:
                count = 0
                for anchor in anchor_list:
                    if domain in anchor and count < domain_contain_limit:
                        is_in_anchor = True

                    # if not MajesticFilter._is_valid_ISO8859_1_str(anchor):
                    #     raise ValueError("anchor contains invalid western language word: {0:s}.".format(anchor,))
                    for spam in self._spam_anchor:
                        pattern = re.compile(spam, re.IGNORECASE)
                        if re.search(pattern, anchor):
                        #if spam in anchor:
                            raise ValueError("anchor {0:s} is in spam word {1:s}".format(anchor, spam))
                    count += 1

            if not is_in_anchor:
                raise ValueError("anchor does not have the domain name in top {0:d} results.".format(domain_contain_limit,))

            return True

        domain = "bbc.co.uk"
        print(isOK(domain))