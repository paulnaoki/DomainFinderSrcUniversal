import threading
from DomainFinderSrc.MiniServer.Common.SocketCommands import Server, ServerCommand, CommandProcessor, CommandStruct, \
    ServerStatus
from DomainFinderSrc.MiniServer.Common.StreamSocket import StreamSocket
from DomainFinderSrc.Utilities.Serializable import Serializable


class MiningController(threading.Thread):
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
            if isinstance(self.server.address, dict):
                self.server.address = Serializable.get_deserialized(self.server.address)
            s.connect((self.server.address.address, self.server.address.port))
            return True
        except Exception as e:
            print(e)
            return False

    def get_status(self):
        status_cmd = CommandStruct(cmd=ServerCommand.Com_Status)
        response = self.processor.check_response_ex(status_cmd)
        response_data = response[1].data
        if isinstance(response_data, dict):
            response_data = Serializable.get_deserialized(response_data)
        if not response[0]:
            raise ValueError("get status failed")
        elif response_data is not None and isinstance(response_data, ServerStatus):
            if isinstance(self.out_data, type([])):
                self.out_data.append(response_data)
            self.server.status = response_data

    def send_data(self):
        data_cmd = CommandStruct(cmd=ServerCommand.Com_Data, data=self.in_data)
        response = self.processor.check_response_ex(data_cmd)
        if not response[0]:
            raise ValueError("send data failed")

    def get_data(self):
        get_data_cmd = CommandStruct(cmd=ServerCommand.Com_Get_Data)
        response = self.processor.check_response_ex(get_data_cmd)
        outdata = response[1].data
        if not response[0]:
            raise ValueError("get data failed")
        else:
            if isinstance(self.out_data, type([])):
                self.out_data.append(outdata)

    def stop_slave(self):
        stop_mining_cmd = CommandStruct(cmd=ServerCommand.Com_Stop_Mining)
        response = self.processor.check_response_ex(stop_mining_cmd)
        if not response[0]:
            raise ValueError("stop slave failed")

    def setup_slave(self):
        setup_cmd = CommandStruct(cmd=ServerCommand.Com_Setup, data=self.in_data)
        response = self.processor.check_response_ex(setup_cmd)
        if not response[0]:
            raise ValueError("send data failed")

    def clear_cache(self):
        stop_mining_cmd = CommandStruct(cmd=ServerCommand.Com_Clear_Cache)
        response = self.processor.check_response_ex(stop_mining_cmd)
        if not response[0]:
            raise ValueError("clear cache failed")

    def run(self):
        try:
            start_cmd = CommandStruct(ServerCommand.Com_Start)
            stop_cmd = CommandStruct(ServerCommand.Com_Stop)
            if self.is_connection_ok() and self.processor.check_response_ex(start_cmd)[0]:
                if self.cmd == ServerCommand.Com_Status:
                    self.get_status()
                elif self.cmd == ServerCommand.Com_Data:
                    self.send_data()
                elif self.cmd == ServerCommand.Com_Get_Data:
                    self.get_data()
                elif self.cmd == ServerCommand.Com_Stop_Mining:
                    self.stop_slave()
                elif self.cmd == ServerCommand.Com_Setup:
                    self.setup_slave()
                elif self.cmd == ServerCommand.Com_Clear_Cache:
                    self.clear_cache()
                else:
                    pass
            try:  # the last call may have exception due to network connection problem
                self.processor.check_response_ex(stop_cmd)
            except:
                pass

        except Exception as ex:
            print(ex)
            pass