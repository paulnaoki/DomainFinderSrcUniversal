import socketserver
from DomainFinderSrc.MiniServer.Common.MiningTCPServer import MiningTCPServer
from DomainFinderSrc.MiniServer.Common.SocketCommands import CommandStruct, CommandProcessor, ServerCommand
from DomainFinderSrc.Utilities.Serializable import Serializable
from threading import Thread, Event


class ServerRequestHandler(Thread):
    def __init__(self):
        self._internal_stop_event = Event()
        Thread.__init__(self)

    def run(self):
        raise NotImplementedError

    def terminate(self):
        self._internal_stop_event.set()

    def handle_request(self, cmd: CommandStruct) -> Serializable or bool:
        raise NotImplementedError


class SimpleServerHandler(socketserver.StreamRequestHandler):

    def handle(self):
        self.send_and_receive()

    def handle_request(self, cmd: CommandStruct):
        s = self.server.addtional_obj
        if isinstance(s, ServerRequestHandler):
            result = s.handle_request(cmd)
            if isinstance(result, Serializable) or isinstance(result, bool):
                return result
            else:
                return False
        else:
            return False

    def send_and_receive(self):
        in_buffer = self.rfile
        out_buffer = self.wfile
        command = CommandProcessor.receive_command(in_buffer)
        #print("process cmd: ", command.cmd)
        if command is not None:
            reply = CommandStruct(cmd=ServerCommand.Com_ReplyOK)
            if command.cmd == ServerCommand.Com_Start:
                #print("start conversation:")
                pass
            elif command.cmd == ServerCommand.Com_Stop:
                #print("end conversation:")
                return
            else:
                server_handle_result = self.handle_request(command)
                if isinstance(server_handle_result, Serializable):
                    reply.data = server_handle_result
                elif isinstance(server_handle_result, bool) and server_handle_result:
                    pass
                else:
                    reply.cmd = ServerCommand.Com_ReplyError
                    reply.data = "command is not valid, please try again"
            CommandProcessor.send_command(out_buffer, reply)

            self.send_and_receive()


def abstract_main(server_handler: ServerRequestHandler,
                  HOST=MiningTCPServer.DefaultListenAddr, PORT=MiningTCPServer.DefaultListenPort):
    server_handler.start()
    print("server running at: " + HOST + " port: " + str(PORT))
    # Create the server, binding to localhost on port 9999
    server = MiningTCPServer((HOST, PORT), SimpleServerHandler, arg=server_handler)
    server.serve_forever()
