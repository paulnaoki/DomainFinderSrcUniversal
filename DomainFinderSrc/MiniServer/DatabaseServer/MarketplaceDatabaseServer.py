import socketserver
from DomainFinderSrc.MiniServer.Common.MiningTCPServer import MiningTCPServer
from DomainFinderSrc.MiniServer.Common.SocketCommands import *


class MarketplaceDBRequestHandler(socketserver.StreamRequestHandler):
    def handle(self):
        self.send_and_receive()

    def send_and_receive(self):
        in_buffer = self.rfile
        out_buffer = self.wfile
        s = self.server.addtional_obj
        command = CommandProcessor.receive_command(in_buffer)

