from threading import Thread, Event, RLock
import time
from DomainFinderSrc.MiniServer.Common.AbstractServer import ServerRequestHandler
from DomainFinderSrc.MiniServer.Common.SocketCommands import CommandStruct
from DomainFinderSrc.Utilities.Serializable import Serializable, NamedMutableSequence
from .TaskControl import CrawlTaskController
from DomainFinderSrc.MiniServer.Common.SocketCommands import ServerType
from DomainFinderSrc.MiniServer.DatabaseServer.MarketplaceDBManager import MarketplaceDBManager,\
    market_place_db_addr, market_place_skeleton_db_addr


class CentralProcessingUnit(ServerRequestHandler):
    def __init__(self):
        ServerRequestHandler.__init__(self)
        self._market_place_manager = MarketplaceDBManager(stop_event=self._internal_stop_event,
                                                          db_addr=market_place_db_addr,
                                                          skeleton_db_addr=market_place_skeleton_db_addr,
                                                          update_time_hour=1)
        # self._task_controller = CrawlTaskController(self._internal_stop_event, self)

    def handle_request(self, cmd: CommandStruct):
        if cmd.target == ServerType.ty_Marketplace_Database:
            return self._market_place_manager.handle_request(cmd)
        else:
            return False

    def run(self):
        self._market_place_manager.start()
        while not self._internal_stop_event.is_set():
            time.sleep(1)
        if self._market_place_manager.is_alive():
            self._market_place_manager.join()
