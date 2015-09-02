from unittest import TestCase
from DomainFinderSrc.Scrapers.MatrixFilter import *
from DomainFinderSrc.Scrapers.MatrixFilterControl import *
from multiprocessing import Event
import queue


class FilterTest(TestCase):
    def testArchiveProfile(self):
        input_param ={"input_queue": queue.Queue(), "output_queue": queue.Queue(), "stop_event": Event()}
        archive_filter = ArchiveOrgFilter(**input_param)
        links = FileIO.FileHandler.read_lines_from_file("/Users/superCat/Desktop/PycharmProjectPortable/test/archive_domain_test.txt")
        for link in links:
            site = FilteredDomainData(domain=link)
            archive_filter.process_data(data=site, )
