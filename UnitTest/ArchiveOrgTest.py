from unittest import TestCase
from DomainFinderSrc.ArchiveOrg.ProfileExtract import ArchiveOrg


class ArchiveOrgTest(TestCase):
    def testGettingLinks(self):
        info = ArchiveOrg.get_url_info("http://susodigital.com", min_size=2, limit=100)
        for item in info:
            link = ArchiveOrg.get_archive_link(item)
            print(link)
