import threading
from DomainFinderSrc.MiniServer.Common.SocketCommands import Server, ServerCommand, CommandProcessor, CommandStruct, ServerStatus
from DomainFinderSrc.MiniServer.Common.StreamSocket import StreamSocket
from DomainFinderSrc.Utilities.Serializable import Serializable


class AbstractClient(threading.Thread):

    def __init__(self, target_server: Server, cmd: str=ServerCommand.Com_Start, target: str="",
                 in_data: Serializable=None, out_data: []=None):
        threading.Thread.__init__(self)
        self.server = target_server
        self.cmd = cmd
        self.in_data = in_data
        self.out_data = out_data
        self.target = target
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

    @property
    def handler_map(self) -> dict:  # override this map
        inner_map = {}
        return inner_map

    def prototype_return_data(self, cmd: str):
        get_data_cmd = CommandStruct(cmd=cmd, target=self.target, data=self.in_data)
        response = self.processor.check_response_ex(get_data_cmd)
        outdata = response[1].data
        if not response[0]:
            raise ValueError("prototype_return_data: get data failed")
        else:
            if isinstance(self.out_data, list):
                self.out_data.append(outdata)

    def prototype_one_way(self, cmd: str):
        data_cmd = CommandStruct(cmd=cmd, target=self.target,  data=self.in_data)
        response = self.processor.check_response_ex(data_cmd)
        if not response[0]:
            raise ValueError("prototype_one_way: command failed")

    def get_status(self):
        status_cmd = CommandStruct(cmd=ServerCommand.Com_Status)
        response = self.processor.check_response_ex(status_cmd)
        response_data = response[1].data
        if isinstance(response_data, dict):
            response_data = Serializable.get_deserialized(response_data)
        if not response[0]:
            raise ValueError("get status failed")
        elif response_data is not None and isinstance(response_data, ServerStatus):
            if isinstance(self.out_data, list):
                self.out_data.append(response_data)
            self.server.status = response_data

    def run(self):
        try:
            handler = self.handler_map.get(self.cmd)
            if handler is not None:
                start_cmd = CommandStruct(ServerCommand.Com_Start)
                stop_cmd = CommandStruct(ServerCommand.Com_Stop)
                if self.is_connection_ok() and self.processor.check_response_ex(start_cmd)[0]:
                    handler()
                try:  # the last call may have exception due to network connection problem
                    self.processor.check_response_ex(stop_cmd)
                except:
                    pass

        except Exception as ex:
            print(ex)
            pass
