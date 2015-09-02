from unittest import TestCase
from DomainFinderSrc.MiniServer.DomainMiningSlaveServer import MiningSlaveServer
from DomainFinderSrc.MiniServer.DomainMiningMasterServer import MiningMasterServer


class ServerTest(TestCase):
    def testSlave(self):
        MiningSlaveServer.main(PORT=9999)

    def testHost(self):
        MiningMasterServer.main(PORT=9998)