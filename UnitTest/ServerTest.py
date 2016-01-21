from unittest import TestCase
from DomainFinderSrc.MiniServer.DomainMiningSlaveServer import MiningSlaveServer
from DomainFinderSrc.MiniServer.DomainMiningMasterServer import MiningMasterServer
from DomainFinderSrc.Scrapers.SiteCheckProcessManager import SiteCheckProcessManager
import time
from DomainFinderSrc.MiniServer.CpuServer import CpuServer


class ServerTest(TestCase):
    def testSlave(self):
        MiningSlaveServer.main(PORT=9999)

    def testHost(self):
        MiningMasterServer.main(PORT=9998)

    def testCpuServer(self):
        CpuServer.main(PORT=9999)

    def testSlaveObj(self):
        site_list = ["http://www.bbc.co.uk/", "techcrunch.com", "mashable.com/category/tech/", "www.techradar.com/",
                     "www.independent.co.uk/life-style/gadgets-and-tech/", "www.theguardian.com/uk/technology",
                     "www.septitech.com/", "www.emosaustin.com/tech-n9ne-special-effects-tour"]
        mananger = SiteCheckProcessManager(job_name="Test", concurrent_page=20, max_page_per_site=100)
        mananger.put_to_input_queue(site_list)
        mananger.start()
        while True:
            time.sleep(1)
