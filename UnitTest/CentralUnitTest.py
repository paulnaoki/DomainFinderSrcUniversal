from DomainFinderSrc.MiniServer.DatabaseServer.MarketplaceDBManager import *
from DomainFinderSrc.MiniServer.CpuServer.CentralProcessing import CrawlTaskController, CentralProcessingUnit, CommandStruct
from unittest import TestCase
from DomainFinderSrc.MiniServer.Common.SocketCommands import ServerType, ServerCommand


class controlUnitTest(TestCase):
    def testHandleMarketplaceData(self):
        control = CentralProcessingUnit()
        request = MarketplaceRequst()
        request.TF = 5
        request.TOPIC1 = "Health/General"
        before_cmd = CommandStruct(cmd=ServerCommand.Com_Get_DB_DATA, target=ServerType.ty_Marketplace_Database,
                                   data=request).get_serializable_json()
        cmd = Serializable.get_deserialized_json(before_cmd)
        results = control.handle_request(cmd)
        print(results)

        before_cmd = CommandStruct(cmd=ServerCommand.Com_DataBase_Stats,
                                   target=ServerType.ty_Marketplace_Database).get_serializable_json()
        cmd = Serializable.get_deserialized_json(before_cmd)
        before_results = control.handle_request(cmd).get_serializable_json()
        after_results = Serializable.get_deserialized_json(before_results)
        print(str(after_results))
