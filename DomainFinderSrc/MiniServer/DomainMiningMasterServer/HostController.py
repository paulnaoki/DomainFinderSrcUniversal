import threading
from DomainFinderSrc.MiniServer.Common.SocketCommands import *
from DomainFinderSrc.MiniServer.Common.StreamSocket import StreamSocket


class HostController(threading.Thread):
    def __init__(self, target_server: Server, cmd: str=ServerCommand.Com_Start,
                 in_data: Serializable=None, out_data: []=None):
        threading.Thread.__init__(self)
        self.server = target_server
        self.cmd = cmd
        self.in_data = in_data
        self.out_data = out_data
        self.sock = StreamSocket()
        self.processor = CommandProcessor(self.sock.rfile, self.sock.wfile)

    def is_connection_ok(self):
        try:
            s = self.sock.get_connection()
            s.connect((self.server.address.address, self.server.address.port))
            return True
        except Exception as e:
            print(e)
            return False

    def get_status(self):
        status_cmd = CommandStruct(cmd=ServerCommand.Com_Status)
        response = self.processor.check_response_ex(status_cmd)
        outdata = response[1].data
        if not response[0]:
            print("get status failed")
        elif not isinstance(outdata, MiningList):
            print("output data type is wrong")
        else:
            if isinstance(self.out_data, type([])):
                self.out_data.append(outdata)
            self.server.status = outdata

    def stop_mining(self):
        stop_mining_cmd = CommandStruct(cmd=ServerCommand.Com_Stop_Mining)
        response = self.processor.check_response_ex(stop_mining_cmd)
        if not response[0]:
            raise ValueError("send data failed")

    def clear_cashe(self):
        cmd = CommandStruct(cmd=ServerCommand.Com_Clear_Cache)
        response = self.processor.check_response_ex(cmd)
        if not response[0]:
            raise ValueError("send data failed")

    def add_slave(self):
        if self.in_data is None:
            print("input data is None")
        cmd = CommandStruct(cmd=ServerCommand.Com_Add_Slave, data=self.in_data)
        response = self.processor.check_response_ex(cmd)
        if not response[0]:
            print("send data failed")

    def del_slave(self):
        if self.in_data is None:
            raise ValueError("input data is None")
        cmd = CommandStruct(cmd=ServerCommand.Com_Del_Slave, data=self.in_data)
        response = self.processor.check_response_ex(cmd)
        if not response[0]:
            raise ValueError("send data failed")

    def database_status(self):
        cmd = CommandStruct(cmd=ServerCommand.Com_DataBase_Status)
        response = self.processor.check_response_ex(cmd)
        outdata = response[1].data
        if not response[0]:
            raise ValueError("send data failed")
        elif not isinstance(outdata, MiningList):
            raise ValueError("Database data is wrong")
        else:
            if isinstance(self.out_data, type([])):
                self.out_data.append(outdata)

    def get_db_data(self):
        cmd = CommandStruct(cmd=ServerCommand.Com_Get_DB_DATA, data=self.in_data)
        response = self.processor.check_response_ex(cmd)
        outdata = response[1].data
        if not response[0]:
            raise ValueError("send data failed")
        elif not isinstance(outdata, MiningList):
            raise ValueError("Database data is wrong")
        else:
            if isinstance(self.out_data, type([])):
                self.out_data.append(outdata)

    def set_db_filter(self):
        cmd = CommandStruct(cmd=ServerCommand.Com_Set_DB_Filter, data=self.in_data)
        response = self.processor.check_response_ex(cmd)
        if not response[0]:
            raise ValueError("send data failed")

    def remove_db(self):
        cmd = CommandStruct(cmd=ServerCommand.Com_Remove_DB, data=self.in_data)
        response = self.processor.check_response_ex(cmd)
        if not response[0]:
            raise ValueError("send data failed")

    def get_progress(self):
        cmd = CommandStruct(cmd=ServerCommand.Com_Progress)
        response = self.processor.check_response_ex(cmd)
        outdata = response[1].data
        if not response[0]:
            raise ValueError("send data failed")
        elif not isinstance(outdata, PrograssData):
            raise ValueError("output value is Wrong")
        else:
            if isinstance(self.out_data, type([])):
                self.out_data.append(outdata)

    def setup_host(self):
        cmd = CommandStruct(cmd=ServerCommand.Com_Setup, data=self.in_data)
        response = self.processor.check_response_ex(cmd)
        if not response[0]:
            raise ValueError("setup host failed")

    def start_filtering(self):
        cmd = CommandStruct(cmd=ServerCommand.Com_Start_Filter, data=self.in_data)
        response = self.processor.check_response_ex(cmd)
        if not response[0]:
            raise ValueError("setup host failed")

    def add_seed(self):
        cmd = CommandStruct(cmd=ServerCommand.Com_Add_Seed, data=self.in_data)
        response = self.processor.check_response_ex(cmd)
        if not response[0]:
            raise ValueError("add seeds failed")

    def run(self):
        try:
            start_cmd = CommandStruct(ServerCommand.Com_Start)
            stop_cmd = CommandStruct(ServerCommand.Com_Stop)
            if self.is_connection_ok() and self.processor.check_response_ex(start_cmd)[0]:
                if self.cmd == ServerCommand.Com_Status: # setup and start minging
                    self.get_status()
                elif self.cmd == ServerCommand.Com_Stop_Mining:
                    self.stop_mining()
                elif self.cmd == ServerCommand.Com_Add_Slave:
                    self.add_slave()
                elif self.cmd == ServerCommand.Com_Del_Slave:
                    self.del_slave()
                elif self.cmd == ServerCommand.Com_DataBase_Status:
                    self.database_status()
                elif self.cmd == ServerCommand.Com_Progress:
                    self.get_progress()
                elif self.cmd == ServerCommand.Com_Setup:
                    self.setup_host()
                elif self.cmd == ServerCommand.Com_Start_Filter:
                    self.start_filtering()
                elif self.cmd == ServerCommand.Com_Set_DB_Filter:
                    self.set_db_filter()
                elif self.cmd == ServerCommand.Com_Add_Seed:
                    self.add_seed()
                elif self.cmd == ServerCommand.Com_Get_DB_DATA:
                    self.get_db_data()
                elif self.cmd == ServerCommand.Com_Clear_Cache:
                    self.clear_cashe()
                elif self.cmd == ServerCommand.Com_Remove_DB:
                    self.remove_db()
                else:
                    pass
            try:  # the last call may have exception due to network connection problem
                self.processor.check_response_ex(stop_cmd)
            except:
                pass

        except Exception as ex:
            print(ex)


