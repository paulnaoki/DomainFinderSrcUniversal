from DomainFinderSrc.MiniServer.Common.SocketCommands import ServerCommand
from DomainFinderSrc.MiniServer.Common.AbstractClient import AbstractClient


class CpuClient(AbstractClient):
    
    def __init__(self, *args, **kwargs):
        AbstractClient.__init__(*args, **kwargs)

    @property
    def handler_map(self) -> dict:  # override this map
        inner_map = {ServerCommand.Com_DataBase_Stats, self.get_db_stats,
                     ServerCommand.Com_Add_DB_DATA, self.add_db_data,
                     ServerCommand.Com_Get_DB_DATA, self.get_db_data,
                     ServerCommand.Com_Remove_DB_DATA, self.remove_db_data,
                     ServerCommand.Com_Add_Task, self.add_task,
                     ServerCommand.Com_Get_Task, self.get_task,
                     ServerCommand.Com_Status, self.get_status,
                     }
        return inner_map

    def get_db_stats(self):
        self.prototype_return_data(ServerCommand.Com_DataBase_Stats)

    def get_db_data(self):
        self.prototype_return_data(ServerCommand.Com_Get_DB_DATA)

    def add_db_data(self):
        self.prototype_one_way(ServerCommand.Com_Add_DB_DATA)

    def remove_db_data(self):
        self.prototype_one_way(ServerCommand.Com_Remove_DB_DATA)

    def add_task(self):
        self.prototype_one_way(ServerCommand.Com_Add_Task)

    def get_task(self):
        self.prototype_return_data(ServerCommand.Com_Get_Task)
