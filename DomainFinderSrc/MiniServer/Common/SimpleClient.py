from DomainFinderSrc.MiniServer.Common.SocketCommands import ServerCommand, CommandStruct
from DomainFinderSrc.MiniServer.Common.AbstractClient import AbstractClient


class SimpleClient(AbstractClient):
    def __init__(self, has_return_data: bool, *args, **kwargs):
        self._has_return_data = has_return_data
        AbstractClient.__init__(self, *args, **kwargs)

    def run(self):
        try:
            handler = self.prototype_one_way if not self._has_return_data else self.prototype_return_data
            if handler is not None:
                start_cmd = CommandStruct(ServerCommand.Com_Start)
                stop_cmd = CommandStruct(ServerCommand.Com_Stop)
                if self.is_connection_ok() and self.processor.check_response_ex(start_cmd)[0]:
                    handler(self.cmd)
                try:  # the last call may have exception due to network connection problem
                    self.processor.check_response_ex(stop_cmd)
                except:
                    pass

        except Exception as ex:
            print(ex)
            pass

