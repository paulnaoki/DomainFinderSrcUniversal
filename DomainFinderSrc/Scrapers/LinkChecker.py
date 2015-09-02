import os.path
from urllib.parse import urlsplit
import socket
import requests
import tldextract
from tornado.ioloop import IOLoop
from requests import adapters, Response
from DomainFinderSrc.Scrapers.WebRequestCommonHeader import WebRequestCommonHeader
from DomainFinderSrc.Scrapers.NonBlockingRequest import AsyncHandler
from pythonwhois import net, parse
import datetime
from DomainFinderSrc.Utilities.Logging import ErrorLogger
import re
import bs4


class ResponseCode:
    LinkOK = 200
    LinkRedirect = 301
    LinkError = 404
    DNSError = 999
    NoDNSError = 998
    Notknown = 997

    #the following is not response code, but used in database
    MightBeExpired = 1000
    Expired = 1001
    Ignore = 1002
    Filtered = 1003
    Bought = 1004

    # generic code
    LinkBroken = 2
    All = 0
    LinkNotBroken = 1

    @staticmethod
    def is_link_broken(response_code: int):
        if response_code == ResponseCode.LinkError or response_code == ResponseCode.DNSError:
            return True
        else:
            return False

    @staticmethod
    def domain_might_be_expired(response_code: int):
        if response_code > 998:
            return True
        else:
            return False

valid_domain_pattern = re.compile('^[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,10}$', re.IGNORECASE)
status_pattern = re.compile('\s?(status)\s?:?(\s?.*)\s?', re.IGNORECASE)
status_value_pattern = re.compile("(\s(?<!not )available)", re.IGNORECASE)
available_pattern0 = re.compile("^(no match|not found|no data found)", re.IGNORECASE)
available_pattern1 = re.compile("\s(is available for purchase)", re.IGNORECASE)
redemption_pattern = re.compile("(redemptionperiod|pendingdelete)", re.IGNORECASE)
other_official_status_pattern = re.compile("(www.icann.org/epp#)", re.IGNORECASE)


class LinkChecker:

    max_http_connection = 2
    max_pool_size = 2
    common_res_ex = [".js", ".css", ".jpeg", ".jpg", ".png", "bmp", ".zip", ".pdf", ".txt", ".doc", ".docx",
                     ".json", ".tar.gz", ".tar.bz2", ".a", ".ar", ".cpio", ".shar", ".iso", ".lbr", ".mar", ".tar",
                     ".bz2", ".f", ".gz", ".7z", ".s7z", ".ace", ".dmg", ".jar", ".apk"]
    common_img_ex = [".jpg", ".png", ".jpeg", ".bmp", ".ico", ".gif"]
    common_html_page_ex = [".html", ".htm", ".xhtml", ".jhtml", ".shtml", ".asp", ".pl", ".cgi"
                           ".jsp", ".jspx", ".php", ".awp", ".stm,", ".jspa", ".xml", ".aspx"]
    common_font_ex = [".eot", ".woff", ".ttf", ".svg", ".otf", ".ttc", ]
    #forbidden_list = ["google.", "twitter.", "yahoo.", "facebook.", "microsoft.", "youtube.", "baidu.", "taobao.",
     #                 "linkedin.", "pinterest.", "tumblr.", "instagram.", "vk.", "flickr.", "wikipedia.org", "bbc."]
    forbidden_list = ["google.", "baidu.", "taobao.", "sina.", "tmail."]

    @staticmethod
    def get_common_request_session(retries=0, redirect=2) ->requests.Session:
        s = requests.Session()
        a = requests.adapters.HTTPAdapter(max_retries=retries, pool_connections=LinkChecker.max_http_connection,
                                          pool_maxsize=LinkChecker.max_pool_size)
        s.max_redirects = redirect
        s.mount('http', adapter=a)
        return s

    @staticmethod
    def get_domain_link(full_link: str)->str:
        if not full_link.startswith("http"):
            full_link = "http://"+full_link
        parsed = urlsplit(full_link)
        return parsed[0]+"://"+parsed[1]

    @staticmethod
    def get_root_domain(full_link: str, use_www=True) ->(False, str, str, str, str, str, str):
        """
        get the root domain from url
        :param full_link: e.g "http://www.google.com"
        :return:Tuple(True is the domain is root domain else Sub-domain, the real root domain, link to root domain,
        link to sub.domain, sub.domain, suffix of the domain, domain pure)
        """
        scheme = "http"
        if full_link.startswith("https"):
            scheme = "https"
            #scheme, target_domain, a, b, c = urlsplit(full_link)
            #scheme = urlsplit(full_link)[0]
        scheme += "://"
        #ext = tldextract.extract(target_domain)
        ext = tldextract.extract(full_link)
        root = ext.domain+"."+ext.suffix
        prefix = "www."
        if len(ext.domain) == 0 or len(ext.suffix) == 0:
            return False, "", "", "", "", "", ""
        elif ext.subdomain is None or len(ext.subdomain) == 0:
            if use_www:
                return True, root, scheme+prefix+root, scheme+prefix+root, prefix+root, ext.suffix, ext.domain
            else:
                return True, root, scheme+root, scheme+root, root, ext.suffix, ext.domain
        else:
            sub_domain = ext.subdomain+"."+root
            if use_www:
                return False, root, scheme+prefix+root, scheme+sub_domain, sub_domain, ext.suffix, ext.domain
            else:
                return False, root, scheme+root, scheme+sub_domain, sub_domain, ext.suffix, ext.domain

    @staticmethod
    def get_domain(full_link: str)->str:
        if not full_link.startswith("http"):
            full_link = "http://"+full_link
        parsed = urlsplit(full_link)
        return parsed[1]

    @staticmethod
    def is_domain_forbidden(full_link: str):
        root_domain = LinkChecker.get_root_domain(full_link)[1]
        forbidden = False
        for item in LinkChecker.forbidden_list:
            if item in root_domain:
                forbidden = True
                break
        return forbidden

    @staticmethod #use this one
    def is_domain_DNS_OK(link: str, force_direct_check=False):
        try:
            domain = link
            if force_direct_check:
                domain = LinkChecker.get_domain(link)
            if domain == "" or domain is None:
                return False
            #sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #sock.settimeout(5)
            #addr =sock.connect((domain, 80))
            #addr = sock.connect()
            #socket.setdefaulttimeout(5)
            addr = socket.getaddrinfo(domain, 80)
            return True if addr is not None else False
        except:
            return False

    @staticmethod
    def is_domain_DNS_OK_v1(link: str, force_direct_check=False):
        """
        :param domain: domain name with scheme, e.g: www.google.com, or http://www.google.com, or www.google.com/page1
        :return:True if the domain has address, else False
        """
        try:
            domain = link
            if force_direct_check:
                domain = LinkChecker.get_domain(link)
            if domain == "" or domain is None:
                return False
            sock = socket.create_connection((domain, 80), timeout=5)
            #sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #sock.settimeout(5)
            #addr =sock.connect((domain, 80))
            #addr = sock.connect()
            #socket.setdefaulttimeout(5)
            connection_ok = True if sock is not None else False
            sock.close()
            return connection_ok
        except Exception as ex:
            print(ex)
            return False

    @staticmethod
    def is_domain_DNS_OK_V2(link: str, force_direct_check=False):
        try:
            domain = link
            if force_direct_check:
                domain = LinkChecker.get_domain(link)
            if domain == "" or domain is None:
                return False
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((domain, 80))
            sock.close()
            return True if result == 0 else False
            #sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #sock.settimeout(5)
            #addr =sock.connect((domain, 80))
            #addr = sock.connect()
            #socket.setdefaulttimeout(5)

        except Exception as ex:
            print(ex)
            return False

    @staticmethod
    def check_whois_V1(domain:str):
        if domain is not None and len(domain) > 0:
            try:
                server = net.get_root_server(domain)
                raw = net.get_whois_raw(domain, server=server)
                parsed = parse.parse_raw_whois(raw_data=raw)
                if len(parsed) > 0:
                    return False, None, True
                else:
                    return True, None, True
            except:
                return False, None, True

    @staticmethod
    def is_domain_available_whois(domain: str) -> (bool, bool):
        """
        availability check with whois.
        :param domain: domain name to check, e.g: google.com.
        make sure the domain is in lower case in the first place.
        :return:True if the domain is available, True if domain in is redemption
        """
        if domain is not None and len(domain) > 0:
            try:
                match = re.match("^[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,10}$", domain)
                if match is None:
                    raise ValueError("domain name error.")
                #gr0 = match.group(0)
                server = net.get_root_server(domain)
                raw_data = net.get_whois_raw(domain, server=server)
                available = False
                is_redemption = False
                force_break = False
                status = ""
                fomat_line = ""
                all_lines = []
                patterns = [status_pattern, available_pattern0, available_pattern1]
                raw_data = [segment.replace("\r", "") for segment in raw_data] # Carriage returns are the devil
                for segment in raw_data:
                    all_lines += str(segment).splitlines()

                for pattern in patterns:
                    # if status is not None and len(status) > 0:
                    #     break
                    if available or is_redemption or force_break:
                        break
                    for line in all_lines:
                        if len(line) == 0:
                            continue
                        temp = line.strip()
                        if temp.endswith(":"):
                            fomat_line = temp
                            continue
                        if fomat_line.endswith(":"):
                            fomat_line += temp
                        else:
                            fomat_line = temp
                        if fomat_line.startswith("%"):
                            continue
                        else:
                            fomat_line = fomat_line.lower()
                            if pattern is status_pattern:
                                match_status = re.search(status_pattern, fomat_line)
                                if match_status is not None:
                                    status = match_status.group(2)
                                    if status is not None and len(status) > 0:
                                        if re.search(status_value_pattern, status) is not None:
                                            available = True
                                            break
                                        elif re.search(redemption_pattern, status) is not None:
                                            is_redemption = True
                                            break
                                        elif re.search(other_official_status_pattern, status) is not None:
                                            force_break = True
                                            break
                            elif re.search(pattern, fomat_line) is not None:
                                available = True
                                break

                # if status is not None and len(status) > 0:
                #     if re.search(status_value_pattern, status) is not None:
                #         available = True
                #     elif re.search(redemption_pattern, status) is not None:
                #         is_redemption = True

                return available, is_redemption
            except ValueError:
                return False, False
            except Exception as ex:
                ErrorLogger.log_error("LinkChecker", ex, "is_domain_available_whois() " + domain)
                return False, False
        else:
            return False

    @staticmethod
    def check_whois(domain: str):
        """

        :param domain:
        :return: True domain might avaiable to buy now, date time of expire, True if action is 100% sure
        """
        if domain is not None and len(domain) > 0:
            try:
                match = re.match("^[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,10}$", domain)
                if match is None:
                    raise ValueError("domain name error.")
                server = net.get_root_server(domain)
                raw = net.get_whois_raw(domain, server=server)
                parsed = parse.parse_raw_whois(raw_data=raw)
                expire_record = parsed.get("expiration_date")
                name_servers = parsed.get("nameservers")
                if len(parsed) <= 1:
                    return True, None, True
                else:
                    if expire_record is not None and len(expire_record) > 0:
                        temp = expire_record[0]
                    else:
                        if name_servers is None:
                            return True, None, True
                        else:
                            return False, None, False

                    expire_dates = len(expire_record)
                    if expire_dates > 1:
                        for i in range(1, expire_dates):
                            data = expire_record[i]
                            if data > temp:
                                temp = data
                    date = datetime.datetime.utcnow()
                    if temp is not None:
                        if date < temp:
                            #print(domain + " is not expired")
                            return False, temp, True
                        else:
                            if name_servers is None:
                                return True, temp, True
                            else:
                                return True, temp, False
                    else:
                        return True, None, False
            except Exception as ex:
                msg = "error in LinkChecker.check_whois(), checking " + domain
                ErrorLogger.log_error("LinkChecker", ex, msg)
                return False, None, False
        else:
            return False, None, True

    @staticmethod
    def get_valid_link(root_domain: str, link: str, scheme: str="http"):
        hash_index = link.find("#")
        if hash_index >= 0:
            link = link[0: hash_index]
        if link.endswith("/"):
            link = link[:-1]  # remove the last char
        if len(link) == 0:
            return scheme+"://"+root_domain
        if link.startswith("//"):
            return scheme + ":" + link
        if link.startswith("/"):
            return scheme+"://"+root_domain+link
        elif link.startswith("www."):
            return scheme + "://" + link
        elif not link.startswith("http"):
            temp_root = root_domain
            if root_domain.startswith("www."):
                temp_root = root_domain[4:]
            if temp_root in link:
                return scheme+"://"+link
            else:
                return scheme+"://"+root_domain+"/"+link
        else:  # if link start with http
            return link

    @staticmethod
    def is_external_link(root_domain: str, link: str):
        if link.startswith("/"):
            return False
        else:
            localNet = LinkChecker.get_root_domain(link)[1]
            if localNet == root_domain:
                return False
            else:
                return True

    @staticmethod
    def is_external_link_V1(root_domain: str, link: str):
        if link.startswith("/"):
            return False
        else:
            localNet = ""
            if link.startswith("http"):
                localNet = urlsplit(link)[1]
            else:
                localNet = link.split("/")[0]
            if not root_domain.startswith("www."):
                root_domain = "www." + root_domain
            if not localNet.startswith("www."):
                localNet = "www." + localNet
            if localNet == root_domain:
                return False
            else:
                return True

    @staticmethod
    def get_response(link: str, timeout: int=5) -> (int, str):
        """
        :param link: link to check
        :param timeout: set timeout to stop stuck here forever
        :return: tuple(response_code:int, content_type:str)
        """
        return_obj = ResponseCode.DNSError, "unknown"
        s = LinkChecker.get_common_request_session()
        try:
            req = s.head(link, allow_redirects=True, timeout=timeout, headers=WebRequestCommonHeader.get_html_header())
            content_type = req.headers["content-type"]
            return_obj = req.status_code, content_type
        except:
            pass
        finally:
            s.close()
            return return_obj

    @staticmethod
    def get_response_non_block(link: str, loop: IOLoop, timeout: int=5) -> (int, str):
        try:
            handler = AsyncHandler(link, loop=loop, timeout=timeout)
            response = handler.get_response(True)
            if response[1] is not None:
                return response[0], response[1]["Content-Type"]
            else:
                return response[0], "unknown"
        except:
            return ResponseCode.DNSError, "unknown"

    @staticmethod
    def get_page_source_non_block(link: str, loop: IOLoop=None, timeout: int=5) -> str:
        try:
            handler = AsyncHandler(link, loop=loop, timeout=timeout)
            response = handler.get_response()
            if response[2] is not None:
                return response[2]
            else:
                return ""
        except:
            return ""

    @staticmethod
    def get_common_web_resource(link: str, timeout: int=5, retries=0, redirect=3)-> Response:
        s = LinkChecker.get_common_request_session(retries=retries, redirect=redirect)
        return_obj = None
        try:
            return_obj = s.get(link, headers=WebRequestCommonHeader.get_common_header(), timeout=timeout)
        except:
            pass
        finally:
            s.close()
            return return_obj

    @staticmethod
    def get_page_source(link: str, timeout: int=5, retries=0, redirect=2) -> Response:
        s = LinkChecker.get_common_request_session(retries=retries, redirect=redirect)
        return_obj = None
        try:
            return_obj = s.get(link, headers=WebRequestCommonHeader.get_html_header(), timeout=timeout)
            #if isinstance(content, Response):
                # if raw_data:
                #     content.text
                #     return_obj = content.content
                # else:
                #     return_obj = content.text
        except:
            pass
        finally:
            s.close()
            return return_obj

    @staticmethod
    def get_webpage_links_from_source(source: Response, use_lxml_parser=False) -> []:
        """
        parse the page source using beautifulsoup4 by default, unless you are sure that lxml module is present
        :param data: page soure in string
        :param use_lxml_parser: force to use lxml module, which is way faster.
        lxml is not install on Windows for python3.4, call SiteChecker.is_use_lxml_parser to determine
        :return: A list of links in str, webpage links only
        """

        def bs4_parse():
            link_list = []
            soup_html = bs4.BeautifulSoup(source.text)
            anchors = soup_html.find_all("a")
            for anchor in anchors:
                if "href" in anchor.attrs:
                    link = anchor["href"]
                    link_list.append(link)
            return link_list

        def lxml_parse():
            from lxml import html
            tree = html.document_fromstring(source.raw)
            link_list = [x.attrib["href"] for x in tree.xpath("//a[@href]")]
            return link_list

        if use_lxml_parser:
            try:
                results = lxml_parse()
            except:
                results = bs4_parse()
        else:
            results = bs4_parse()

        return results

    @staticmethod
    def get_all_links_from_source(source: Response, use_lxml_parser=False) -> []:
        """
        parse the page source using beautifulsoup4 by default, unless you are sure that lxml module is present
        :param data: page soure in string
        :param use_lxml_parser: force to use lxml module, which is way faster.
        lxml is not install on Windows for python3.4, call SiteChecker.is_use_lxml_parser to determine
        :return: A list of links in str, including css, js, images, webpages
        """
        def bs4_parse():
            link_list = []
            soup_html = bs4.BeautifulSoup(source.text)
            anchors = soup_html.find_all("a")  # links
            for anchor in anchors:
                if "href" in anchor.attrs:
                #if isinstance(anchor, bs4.Tag):
                    link = anchor["href"]
                    link_list.append(link)
            other_links = soup_html.find_all("link")
            for other_link in other_links:
                if "href" in other_link.attrs:
                    link = other_link["href"]
                    link_list.append(link)
            javascripts = soup_html.find_all("script")
            for script in javascripts:
                if "src" in script.attrs:
                    link = script["src"]
                    link_list.append(link)

            return link_list

        def lxml_parse():  # TODO: need to test this
            from lxml import html
            tree = html.document_fromstring(source.raw)
            link_list = [x.attrib["href"] for x in tree.xpath("//a[@href]")]
            return link_list

        if use_lxml_parser:
            try:
                results = lxml_parse()
            except:
                results = bs4_parse()
        else:
            results = bs4_parse()

        return results

    @staticmethod
    def is_link_content_html_page(content_type: str):
        """
        :param content_type: the content-type of request header
        :return: true the type is html
        """
        content = content_type.lower()
        if "text/html" in content or "text/plain" in content:
            return True
        else:
            return False

    @staticmethod
    def get_link_extension(link: str)->str:
        if link is None or link == "":
            return ""
        else:
            paths = os.path.splitext(link)
            ext = paths[1]
            new_link = paths[0]
            if ext != "":
                return LinkChecker.get_link_extension(new_link) + ext
            else:
                return ""

    @staticmethod
    def might_be_link_html_page(link_path: str):
        extension = LinkChecker.get_link_extension(link_path)
        if extension is None or len(extension) == 0:
            return True
        elif extension in LinkChecker.common_html_page_ex:
            return True
        else:
            return False
