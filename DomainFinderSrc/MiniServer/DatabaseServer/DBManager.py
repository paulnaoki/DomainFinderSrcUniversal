import threading
import multiprocessing
from DomainFinderSrc.Utilities import FileIO
from DomainFinderSrc.MiniServer.DatabaseServer.CategoryDB import *
from DomainFinderSrc.MiniServer.Common.SocketCommands import ServerState, MiningList


class DBManagerInterface(threading.Thread):
    def __init__(self, update_time_hour: int, update_process, db_addr: str, skeleton_db_addr: str):
        self.state = ServerState.State_Init
        self._update_process = update_process
        self._db_addr = db_addr
        self._skeleton_db_addr = skeleton_db_addr
        FileIO.FileHandler.create_file_if_not_exist(self._skeleton_db_addr)
        self._update_time_hour = update_time_hour
        self._stop_event = threading.Event()
        self._db_lock = threading.RLock()
        self._skeleton_db_lock = threading.RLock()
        self._skeleton_db_manager = CategoryDBManager(self._skeleton_db_addr)
        threading.Thread.__init__(self)

    def update_db(self):
        with self._db_lock:
            process_db_update = multiprocessing.Process(target=self._update_process)
            process_db_update.start()
            process_db_update.join()
            if process_db_update.is_alive():
                process_db_update.terminate()
            with self._skeleton_db_lock:
                self._skeleton_db_manager = CategoryDBManager(self._skeleton_db_addr)

    def get_db_stats(self) -> MiningList:
        with self._skeleton_db_lock:
            data = self._skeleton_db_manager.categories
        return MiningList("Stats", data=data)

    def get_db_data(self, index=0, count=0, **kwargs) -> MiningList:
        raise NotImplementedError

    def add_db_data(self, data=None, **kwargs):
        raise NotImplementedError

    def update_db_data(self, data=None, **kwargs):
        raise NotImplementedError

    def delete_db_data(self, data=None, **kwargs):
        raise NotImplementedError

    def run(self):
        wait_second = self._update_time_hour * 3600
        wait_second_count = 0
        while not self._stop_event.is_set():
            self.state = ServerState.State_Idle
            if wait_second_count > wait_second:
                wait_second_count = 0
                self.state = ServerState.State_Busy
                self.update_db()
            wait_second_count += 1
