import json
from urllib.parse import urlencode
import requests
from DomainFinderSrc.Utilities.Serializable import Serializable


class ArchiveStruct(Serializable):
    def __init__(self, link: str, date_stamp: str, size: int):
        self.link = link
        self.date_stamp = date_stamp
        self.size = size

    def __str__(self):
        return "link: " + self.link + " time_stamp: " + self.date_stamp + " size: " + str(self.size)


class ArchiveOrg:

    BASE_QUERY_URL = "http://web.archive.org/cdx/search/cdx?"
    BASE_ARCHIVE_URL = "http://web.archive.org/web/"
    @staticmethod
    def get_url_info(link: str, min_size: int, limit: int=-500) ->[]:
        """
        get information about a link
        :param link: the html webpage link in archive
        :param min_size: minimum data length of the file from the link in Kb
        :param limit: number of returning results, positive counting from the begining, negative from the ending.
        :return: A list of archives of the link in ArchiveStruct format, newest first.
        """
        # http://web.archive.org/cdx/search/cdx?url=susodigital.com&output=json
        # &filter=statuscode:200&filter=mimetype:text/html&filter=!length:^([0-9]|[1-9][0-9]|[1-9][0-9][0-9]|[1-2][0-9][0-9][0-9])
        # $&collapse=digest&limit=500&matchType=exact&fl=timestamp,length,original
        if len(link) == 0:
            return []
        # if limit < 1:
        #     limit = 1
        if min_size > 1:
            size_query = "!length:^([0-9]|[1-9][0-9]|[1-9][0-9][0-9]|[1-{0:d}][0-9][0-9][0-9])$".format(min_size-1)
        else:
            size_query = "!length:^([0-9]|[1-9][0-9]|[1-9][0-9][0-9])$"
        archive_dict = {'url': link, 'filter': size_query, 'limit': limit, 'output': 'json',
                        'fl': 'timestamp,length,original', 'collapse': 'digest'}
        first_part = urlencode(archive_dict)
        second_part = urlencode((('filter', 'statuscode:200'), ('filter', 'mimetype:text/html')))
        query = first_part + "&" + second_part
        data = requests.get(ArchiveOrg.BASE_QUERY_URL+query)
        # jsoned = json.loads(str(data.content, encoding="utf-8"))
        jsoned = json.loads(data.text)
        data_len = len(jsoned) - 1
        if data_len > 0:
            result = []
            for time_stamp, length, original_link in jsoned[:-data_len-1:-1]:
                result.append(ArchiveStruct(link=original_link, date_stamp=time_stamp, size=length))
            return result  # newest first
        else:
            return []

    @staticmethod
    def get_domain_urls(link: str, limit: int=2000) ->[]:
        archive_dict = {'url': link, 'limit': limit, 'output': 'json', 'matchType': 'domain',
                        'fl': 'timestamp,length,original', 'collapse': 'urlkey'}
        query = urlencode(archive_dict)
        data = requests.get(ArchiveOrg.BASE_QUERY_URL+query)
        # jsoned = json.loads(str(data.content, encoding="utf-8"))
        jsoned = json.loads(data.text)
        data_len = len(jsoned) - 1
        if data_len > 0:
            result = []
            for time_stamp, length, original_link in jsoned:
                result.append(ArchiveStruct(link=original_link, date_stamp=time_stamp, size=length))
            return result  # newest first
        else:
            return []

    @staticmethod
    def get_archive_link(archive_struct: ArchiveStruct):
        if not archive_struct.link.endswith("/"):
            archive_struct.link += "/"
        return ArchiveOrg.BASE_ARCHIVE_URL + archive_struct.date_stamp + "/" + archive_struct.link