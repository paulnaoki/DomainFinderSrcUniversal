import datetime
import time
import hmac
import base64
import hashlib
import urllib.parse
import binascii
import requests
from requests import adapters
from DomainFinderSrc.SiteConst import SiteAccount
from xml.etree import ElementTree
from collections import defaultdict
# from uritools import uriencode, uricompose


class ServiceUtility:

    @staticmethod
    def get_tag_content(target_tag: str, parent: ElementTree.Element, namespace: str) -> str:
        if parent is None:
            return ""
        else:
            try:
                child = parent.find("{{{0:s}}}{1:s}".format(namespace, target_tag))
                if child is None:
                    return ""
                else:
                    return child.text
            except:
                return ""

    @staticmethod
    def percent_encode_rfc3986(url: str):
        temp = list(url.replace("'", "%27").replace("(", "%28").replace(")", "%29").replace("*", "%2A")\
            .replace("!", "%21").replace("%7e", "~").replace("+", "%20"))
        char_len = len(temp)
        for i in range(0, char_len):
            if temp[i] == '%':
                if i + 1 < char_len and temp[i+1].isalpha():
                    temp[i+1] = temp[i+1].upper()
                if i + 2 < char_len and temp[i+2].isalpha():
                    temp[i+2] = temp[i+2].upper()
        return "".join(temp)




    @staticmethod
    def get_common_request_query(end_point: str, dry_run: bool, action: str, public_access_key: str, private_key: str,
                                       kvargs: dict, version: str="2015-10-01",) -> str:
        """
        http://docs.aws.amazon.com/general/latest/gr/signature-version-2.html
        e.g: http://www.codeproject.com/Articles/175025/Create-URL-for-an-Authenticated-Amazon-EC2-API-Req
        :param dry_run:
        :param action:
        :param public_access_key:
        :param private_key:
        :param version:
        :return:
        """
        time_now = datetime.datetime.utcnow()
        parameters = dict({"Action": action,
                      "DryRun": "true" if dry_run else "false",  # omit this for test
                      "AWSAccessKeyId": public_access_key,
                      "Timestamp": str(time_now.strftime("%Y-%m-%dT%H:%M:%S")),
                      # "Timestamp": "2011-10-03T15:19:30",
                      "SignatureVersion": 2,
                      "SignatureMethod": "HmacSHA256",
                      "Version": version,
        }, **kvargs)
        # parameters.update(kvargs)

        sort = sorted(parameters.items())
            # key=lambda kv_pair: binascii.hexlify(str.encode(kv_pair[0])))
        # for item in sort:
        #     print(item)
        # para_encoded = uriencode(sort)
        # para_encoded2 = uricompose(query=sort)[1:]
        # para_encoded = uriencode("".join(map(lambda x: str(x[0])+"="+str(x[1]), sort)))
        para_encoded = ServiceUtility.percent_encode_rfc3986(urllib.parse.urlencode(sort))
        print(para_encoded)
        # print(para_encoded2)

        str_to_sign = "GET\n"
        str_to_sign += end_point+"\n"
        str_to_sign += "/\n"
        str_to_sign += para_encoded
        # print(str_to_sign)

        #keyBytes =  array.array('B', self.account.APIKey) # [elem.encode("hex") for elem in self.account.APIKey]
        signatureStr = hmac.new(private_key.encode(), str_to_sign.encode(), digestmod=hashlib.sha256).digest()
        signature = base64.b64encode(signatureStr)#.decode("utf-8")

        # parameters.update({"Signature": signature})
        sort.append(("Signature", signature))
        return ServiceUtility.percent_encode_rfc3986(urllib.parse.urlencode(sort))
        # return uricompose(query=sort)[1:]

    @staticmethod
    def get_common_request_query2(end_point: str, dry_run: bool, action: str, public_access_key: str, private_key: str,
                                       kvargs: dict, version: str="2015-10-01",) -> str:
        """
        http://docs.aws.amazon.com/general/latest/gr/signature-version-2.html
        :param dry_run:
        :param action:
        :param public_access_key:
        :param private_key:
        :param version:
        :return:
        """
        time_now = datetime.datetime.utcnow()
        parameters = {"Action": action,
                      "DryRun": "true" if dry_run else "false",  # omit this for test
                      "AWSAccessKeyId": public_access_key,
                      "Timestamp": str(time_now.strftime("%Y-%m-%dT%H:%M:%S")),
                      # "Timestamp": "2011-10-03T15:19:30",
                      "SignatureVersion": 2,
                      "SignatureMethod": "HmacSHA256",
                      "Version": version,
        }
        parameters.update(kvargs)

        # ordered_dict = collections.OrderedDict()
        # print("before sort")
        # for k, v in parameters.items():
        #     kv = k + "=" + str(v)
        #     byte_int = binascii.hexlify(str.encode(k))
        #     print(k, " ", urllib.parse.urlencode({k: v}), " size:", byte_int)
        # print("after sort")
        sort = sorted(parameters.items(),
            key=lambda kv_pair: binascii.hexlify(str.encode(kv_pair[0])))
            # key=lambda kv_pair: binascii.hexlify(str.encode(urllib.parse.urlencode({kv_pair[0]: kv_pair[1]}))))
        for item in sort:
            print(item)
        para_encoded = urllib.parse.urlencode(sort)

        str_to_sign = "GET\n"
        str_to_sign += end_point+"\n"
        str_to_sign += "/\n"
        str_to_sign += para_encoded
        # print(str_to_sign)

        #keyBytes =  array.array('B', self.account.APIKey) # [elem.encode("hex") for elem in self.account.APIKey]
        signatureStr = hmac.new(private_key.encode(), str_to_sign.encode(), digestmod=hashlib.sha256).digest()
        signature = base64.b64encode(signatureStr).decode("utf-8")

        # parameters.update({"Signature": signature})
        sort.append(("Signature", signature))
        return urllib.parse.urlencode(sort)

    @staticmethod
    def make_request(account: SiteAccount, end_point: str, zone: str, action: str, dry_run: bool,
                     parameters: dict, version="2015-10-01", use_https=False, timeout=10) -> ElementTree.Element:
        print("make request:")
        scheme = "https" if use_https else "http"
        region = zone[:-1]
        end_point = end_point.format(region,)
        query = scheme+"://"+end_point+"/?"+ServiceUtility.get_common_request_query(end_point, dry_run, action,
                                                                                    account.AccessID, account.APIKey,
                                                                                    parameters, version)
        print(query)
        s = requests.Session()
        a = requests.adapters.HTTPAdapter(max_retries=0, pool_connections=10,
                                          pool_maxsize=10)
        s.max_redirects = 0
        s.mount(scheme, adapter=a)
        result = ""
        try:
            result = s.get(query, timeout=timeout).text
            print(result)
        except Exception as ex:
            print(ex)
        finally:
            s.close()
            return ElementTree.XML(result)

    @staticmethod
    def get_tag_uri_and_name(elem: ElementTree.Element):
        if elem.tag[0] == "{":
            uri, ignore, tag = elem.tag[1:].partition("}")
        else:
            uri = None
            tag = elem.tag
        return uri, tag


    @staticmethod
    def etree_to_dict(t):
        d = {t.tag: {} if t.attrib else None}
        children = list(t)
        if children:
            dd = defaultdict(list)
            for dc in map(ServiceUtility.etree_to_dict, children):
                for k, v in dc.iteritems():
                    dd[k].append(v)
            d = {t.tag: {k:v[0] if len(v) == 1 else v for k, v in dd.iteritems()}}
        if t.attrib:
            d[t.tag].update(('@' + k, v) for k, v in t.attrib.iteritems())
        if t.text:
            text = t.text.strip()
            if children or t.attrib:
                if text:
                  d[t.tag]['#text'] = text
            else:
                d[t.tag] = text
        return d