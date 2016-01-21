__author__ = 'Paulli'
import requests
from urllib import parse
from DomainFinderSrc.SiteConst import SiteAccount
from DomainFinderSrc.Utilities.Proxy import ProxyStruct


class BuyProxyOrgConst:
    EndPoint = "http://api.buyproxies.org/?"


class BuyProxyOrg:
    def __init__(self, account: SiteAccount, default_port=55555):
        self._account = account
        self._default_port = default_port

    def get_proxies(self, timeout=5):
        pid = self._account.AccessID
        api_key = self._account.APIKey
        request_parameters = {
            "a": "showProxies",
            "pid": pid,
            "key": api_key
        }
        para_encoded = parse.urlencode(request_parameters)
        request_url = BuyProxyOrgConst.EndPoint + para_encoded
        temp = list()
        try:
            response = requests.get(request_url, timeout=timeout)
            proxy_str_list = response.text.split('\n')
            for item in proxy_str_list:
                if len(item) > 0:
                    addr, port, usr_name, password = item.split(':')
                    temp.append(ProxyStruct(addr, int(port), alt_port=self._default_port, user_name=usr_name, psd=password))
        except Exception as ex:
            print(ex)
        finally:
            return temp
