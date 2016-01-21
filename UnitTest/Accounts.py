from DomainFinderSrc.MajesticCom import *
from DomainFinderSrc.SiteConst import *


majestic_account = SiteAccount(siteType=AccountType.Majestic, userID="will@bazookasearch.com", password="baltimore9!",
                      APIkey="1BB1D141D20CAF35D331F086F55C1CEE")
majestic = MajesticCom(majestic_account)


moz_account = SiteAccount(siteType=AccountType.Moz, userID="gpowellmarketing@gmail.com", password="gpowellmarketing",
                        AccessID="mozscape-320a4616a8", APIkey="f03c19321b0973573137288c647b31ea")

moz_account_fake =  SiteAccount(siteType=AccountType.Moz, userID="blearly66149@tutanota.com", password="uTh6peec123",
                        AccessID="mozscape-44a37bfcd5", APIkey="bedefa75b4c17317a94a421108974f1d")

amazon_ec2_account = SiteAccount(siteType=AccountType.AmazonEC2, userID="paulnaokii@gmail.com",
                                 AccessID="AKIAIPA2WM3ILJWR2KSA", APIkey="7EisLQmbOv04ExZM9Fj1rxnmWiKw8wae5shRPDdx")

buy_proxy_org_account = SiteAccount(siteType=AccountType.BuyProxyOrg, userID="paulnaokii@gmail.com", password="iamthe1",
                                    AccessID="49885", APIkey="c0117800a41b5b4b8eaba12e163c608c")