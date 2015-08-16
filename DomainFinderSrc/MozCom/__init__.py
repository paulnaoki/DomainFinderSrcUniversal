from hashlib import sha1
import hmac
import time
import urllib.parse
import base64
import requests
from DomainFinderSrc.SiteConst import SiteAccount
from DomainFinderSrc.Utilities.Proxy import ProxyStruct
import json


class MozConst:
    APIRequestRootDomain = "http://lsapi.seomoz.com/linkscape/url-metrics/"


class MozCom:
    def __init__(self, account: SiteAccount):
        self.account = account
        self.proxy_str = ""
        proxy = account.proxy
        if isinstance(proxy, ProxyStruct):
            if len(proxy.user_name) > 0:
                self.proxy_str = "{0:s}:{1:s}@{2:s}:{3:d}".format(proxy.user_name, proxy.psd, proxy.addr, proxy.port)
            else:
                self.proxy_str = "{0:s}:{1:d}".format(proxy.addr, proxy.port)

    # check example for more at https://github.com/seomoz/SEOmozAPISamples/blob/master/php/signed_authentication_sample.php
    def get_ranking_data(self, link: str) -> int:
        exprire = int(time.time()) + 300 #expired in 5 mins
        str_to_sign = self.account.AccessID + "\n" + str(exprire)
        #keyBytes =  array.array('B', self.account.APIKey) # [elem.encode("hex") for elem in self.account.APIKey]
        signatureStr = hmac.new(self.account.APIKey.encode(), str_to_sign.encode(), sha1).digest()
        signature = base64.b64encode(signatureStr).decode("utf-8")
            #hmac.new(self.account.APIKey, str_to_sign, sha1).digest().encode("base64").rstrip('\n')
        return_cols = "68719476736" #only return domain authority, otherwise you have to AND the other bits
        parameters ={"Cols": return_cols,
                     "AccessID": self.account.AccessID,
                     "Expires": str(exprire),
                     "Signature": signature}
        para_encoded = urllib.parse.urlencode(parameters)
        link_encoded = urllib.parse.quote(link, safe="")
        request_link = MozConst.APIRequestRootDomain + link_encoded + "?" + para_encoded
        # print(request_link)
        if len(self.proxy_str) > 0:
            format_proxy = "http://"+self.proxy_str+"/"
            proxy = {
                "http": format_proxy,  # "http://user:pass@10.10.1.10:3128/"
            }
            response = requests.get(request_link, proxies=proxy)
        else:
            response = requests.get(request_link)
            response.json()
        da_str = json.loads(response.text)["pda"]
        da = int(float(da_str))
        return da






