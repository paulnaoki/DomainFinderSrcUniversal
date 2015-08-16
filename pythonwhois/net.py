import socket
import re
import sys
import select
from codecs import encode, decode
from . import shared


def get_whois_raw(domain, server="", previous=None, rfc3490=True, never_cut=False, with_server_list=False, server_list=None):
    previous = previous or []
    server_list = server_list or []
    # Sometimes IANA simply won't give us the right root WHOIS server
    exceptions = {
        ".ac.uk": "whois.ja.net",
        ".ps": "whois.pnina.ps",
        ".buzz": "whois.nic.buzz",
        ".moe": "whois.nic.moe",
        # The following is a bit hacky, but IANA won't return the right answer for example.com because it's a direct registration.
        "example.com": "whois.verisign-grs.com"
    }

    if rfc3490:
        if sys.version_info < (3, 0):
            domain = encode( domain if type(domain) is unicode else decode(domain, "utf8"), "idna" )
        else:
            domain = encode(domain, "idna").decode("ascii")

    target_server = server
    if len(previous) == 0 and server == "":
        # Root query
        is_exception = False
        for exception, exc_serv in exceptions.items():
            if domain.endswith(exception):
                is_exception = True
                target_server = exc_serv
                break
        if is_exception == False:
            target_server = get_root_server(domain)
    # else:
    #     target_server = server
    if target_server == "whois.jprs.jp":
        request_domain = "%s/e" % domain  # Suppress Japanese output
    elif domain.endswith(".de") and ( target_server == "whois.denic.de" or target_server == "de.whois-servers.net" ):
        request_domain = "-T dn,ace %s" % domain # regional specific stuff
    elif target_server == "whois.verisign-grs.com":
        request_domain = "=%s" % domain # Avoid partial matches
    else:
        request_domain = domain
    response = whois_request(request_domain, target_server)
    new_list = []
    if never_cut:
        # If the caller has requested to 'never cut' responses, he will get the original response from the server (this is
        # useful for callers that are only interested in the raw data). Otherwise, if the target is verisign-grs, we will
        # select the data relevant to the requested domain, and discard the rest, so that in a multiple-option response the
        # parsing code will only touch the information relevant to the requested domain. The side-effect of this is that
        # when `never_cut` is set to False, any verisign-grs responses in the raw data will be missing header, footer, and
        # alternative domain options (this is handled a few lines below, after the verisign-grs processing).
        new_list = [response] + previous
    if target_server == "whois.verisign-grs.com":
        # VeriSign is a little... special. As it may return multiple full records and there's no way to do an exact query,
        # we need to actually find the correct record in the list.
        for record in response.split("\n\n"):
            if re.search("Domain Name: %s\n" % domain.upper(), record):
                response = record
                break
    if not never_cut:
        new_list = [response] + previous
    server_list.append(target_server)
    for line in [x.strip() for x in response.splitlines()]:
        match = re.match("(refer|whois server|referral url|whois server|registrar whois):\s*([^\s]+\.[^\s]+)", line, re.IGNORECASE)
        if match is not None:
            referal_server = match.group(2)
            if referal_server != server and "://" not in referal_server: # We want to ignore anything non-WHOIS (eg. HTTP) for now.
                # Referal to another WHOIS server...
                return get_whois_raw(domain, referal_server, new_list, server_list=server_list, with_server_list=with_server_list)
    if with_server_list:
        return (new_list, server_list)
    else:
        return new_list


def get_common_whois_server(root_domain: str):
    """
    this method is not contained in original package, was added later by me.
    :param root_domain: root domain, eg: google.com
    :return: whois server in str, or None if not found
    """
    parts = root_domain.split(".")
    len_parts = len(parts)
    if len_parts == 2:
        last_part = parts[1]
        return {"com": "whois.verisign-grs.com",
                "org": "whois.pir.org",
                "net": "whois.verisign-grs.com",
                "edu": "whois.educause.edu",
                "biz": "whois.biz",
                "info": "whois.afilias.net",
                "uk": "whois.nic.uk",
                "fr": "whois.nic.fr",
                "de": "whois.denic.de",
                "us": "whois.nic.us",
                "eu": "whois.eu",
                "ca": "whois.cira.ca",
                "pl": "whois.dns.pl",
                "es": "whois.nic.es",
                "it": "whois.nic.it",
                "in": "whois.inregistry.net",
                "cn": "whois.cnnic.cn",
                "jp": "whois.jprs.jp",
                "nl": "whois.domain-registry.nl",
                "tv": "tvwhois.verisign-grs.com",

                }.get(last_part, None)
    elif len_parts == 3:
        last_part = parts[1] + "." + parts[2]
        return {"co.uk": "whois.nic.uk",
                "org.uk": "whois.nic.uk",
                }.get(last_part, None)
    else:
        return None


def get_root_server(domain):
    """
    this method is integrated with get_common_whois_server() by me
    :param domain: root domain, eg: google.com
    :return:
    """
    common_whois = get_common_whois_server(domain)
    if common_whois is None:
        data = whois_request(domain, "whois.iana.org")
        for line in [x.strip() for x in data.splitlines()]:
            match = re.match("refer:\s*([^\s]+)", line)
            if match is None:
                continue
            return match.group(1)
        raise shared.WhoisException("No root WHOIS server found for domain.")
    else:
        return common_whois


def whois_request(domain, server, port=43, timeout=10):
    """
    connect to a whois server, with timeout - modified from source code
    :param domain: domain you wish to connect to
    :param server: whois server the domain might contained in
    :param port: port of whois server
    :param timeout: timeout in second
    :return:
    """
    buff = b""
    try:
        sock = socket.create_connection((server, port), timeout=timeout)
        # sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        # sock.connect((server, port))
        #sock.settimeout(timeout=timeout)
        sock.send(("%s\r\n" % domain).encode("utf-8"))

        while True:
            data = sock.recv(4096)
            if len(data) == 0:
                break
            buff += data
    except Exception as ex:
        if len(buff) == 0:
            raise ex
    finally:
        return buff.decode("utf-8")
