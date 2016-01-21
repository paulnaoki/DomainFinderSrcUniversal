from DomainFinderSrc.MiniServer.DatabaseServer.MarketplaceDBManager import \
    MarketplaceRequst, MarketplaceDBManager, market_place_db_addr, market_place_skeleton_db_addr
from DomainFinderSrc.MiniServer.Common.SocketCommands import ServerCommand, ServerType, Server, ServerAddress, \
    MiningList
from DomainFinderSrc.Utilities.Serializable import Serializable
from unittest import TestCase
from threading import Event
from DomainFinderSrc.MiniServer.Common.SimpleClient import SimpleClient

site_skeleton_db_addr = "/Users/superCat/Desktop/PycharmProjectPortable/Results/MarketplaceSkeletonSites.db"
site_db_addr = "/Users/superCat/Desktop/PycharmProjectPortable/Results/MarketplaceSites.db"
stop_event = Event()


class MarketplaceTest(TestCase):
    def testManagerGetData(self):
        import json
        manager = MarketplaceDBManager(stop_event=stop_event, db_addr=site_db_addr, skeleton_db_addr=site_skeleton_db_addr)
        request = MarketplaceRequst()
        request.TF = 20
        request.TOPIC1 = "Health/General"
        # serialised = request.__class__().get_serializable()
        serialised = json.dumps(request.get_serializable(), ensure_ascii=False)

        request.TF = 10
        parameters = request.__dict__
        print("request is:")
        print(request)
        print(serialised)
        results = manager.handle_request(cmd=ServerCommand.Com_Get_DB_DATA)
        for item in results:
            print(item)

    def test_get_data_by_client(self):

        output_data = []
        server = Server(address=ServerAddress("127.0.0.1", 9999))
        client = SimpleClient(has_return_data=True, target_server=server, cmd=ServerCommand.Com_DataBase_Stats,
                              target=ServerType.ty_Marketplace_Database, out_data=output_data)
        try:
            client.start()
            client.join()
            data = output_data[0]
            if isinstance(data, MiningList):
                for item in data.data:
                    print(str(item))
        except Exception as ex:
            print(ex)