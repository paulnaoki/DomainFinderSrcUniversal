import threading
import multiprocessing
from DomainFinderSrc.Utilities import FileIO
from DomainFinderSrc.MiniServer.DatabaseServer.CategoryDB import *
from DomainFinderSrc.MiniServer.Common.SocketCommands import ServerState, MiningList, ServerCommand, CommandStruct
from threading import Event, RLock
from DomainFinderSrc.MiniServer.Common.AbstractServer import ServerRequestHandler


class DBManagerInterface(ServerRequestHandler):
    def __init__(self, stop_event: Event,  update_time_hour: int, update_process, db_addr: str, skeleton_db_addr: str):
        self._external_stop_event = stop_event
        self.state = ServerState.State_Init
        self._update_process = update_process
        self._db_addr = db_addr
        self._skeleton_db_addr = skeleton_db_addr
        FileIO.FileHandler.create_file_if_not_exist(self._skeleton_db_addr)
        self._update_time_hour = update_time_hour
        self._db_lock = threading.RLock()
        self._skeleton_db_lock = threading.RLock()
        self._skeleton_db_manager = CategoryDBManager(self._skeleton_db_addr)
        ServerRequestHandler.__init__(self)

    def get_update_process_args(self) -> dict:
        raise NotImplementedError

    def update_db(self):
        with self._db_lock:
            process_db_update = multiprocessing.Process(target=self._update_process,
                                                        kwargs=self.get_update_process_args())
            process_db_update.start()
            process_db_update.join()
            if process_db_update.is_alive():
                process_db_update.terminate()
            with self._skeleton_db_lock:
                self._skeleton_db_manager = CategoryDBManager(self._skeleton_db_addr)

    def get_db_stats(self) -> MiningList:
        return_obj = MiningList("DATA")
        with self._skeleton_db_lock:
            data = self._skeleton_db_manager.categories
            return_obj.data = data
        return return_obj

    def get_db_data(self, index=0, count=0, **kwargs) -> MiningList:
        raise NotImplementedError

    def add_db_data(self, data=None, **kwargs) -> bool:
        raise NotImplementedError

    def update_db_data(self, data=None, **kwargs) -> bool:
        raise NotImplementedError

    def delete_db_data(self, data=None, **kwargs) -> bool:
        raise NotImplementedError

    def run(self):
        wait_second = self._update_time_hour * 3600
        wait_second_count = 0
        while not (self._external_stop_event.is_set() or self._internal_stop_event.is_set()):
            self.state = ServerState.State_Idle
            if wait_second_count > wait_second:
                wait_second_count = 0
                self.state = ServerState.State_Busy
                self.update_db()
            wait_second_count += 1

    def handle_request(self, cmd: CommandStruct) -> Serializable or bool:
        data = cmd.data
        code = cmd.cmd
        if code == ServerCommand.Com_Add_DB_DATA and isinstance(data, MiningList):  # incoming data
            return self.add_db_data(data=data)
        elif code == ServerCommand.Com_DataBase_Stats:
            return self.get_db_stats()
        else:
            raise NotImplementedError
