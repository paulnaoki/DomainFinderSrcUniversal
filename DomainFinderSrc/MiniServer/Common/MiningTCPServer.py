import socketserver
from DomainFinderSrc.MiniServer.Common.SocketCommands import ServerAddress


class MiningTCPServer(socketserver.ThreadingTCPServer):
    DefaultListenAddr = "0.0.0.0"
    DefaultListenPort = 9999

    def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True, arg=None):
        socketserver.ThreadingTCPServer.__init__(self, server_address, RequestHandlerClass, bind_and_activate)
        self.addtional_obj = arg

    def get_server(self)->ServerAddress:
        return ServerAddress(self.server_address[0], self.server_address[1])