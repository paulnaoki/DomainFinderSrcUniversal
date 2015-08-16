import socketserver
import threading

from DomainFinderSrc.MiniServer.Common.MiningTCPServer import MiningTCPServer
from DomainFinderSrc.MiniServer.Common.SocketCommands import *
from DomainFinderSrc.Scrapers.SiteTempDataSrc.DataStruct import ScrapeDomainData
from DomainFinderSrc.Scrapers.SiteTempDataSrc.SiteTempDataSrcInterface import OnSiteLink
from DomainFinderSrc.Scrapers.SiteCheckProcessManager import SiteCheckProcessManager
from DomainFinderSrc.Utilities.MachineInfo import MachineInfo


class SlaveAutoScaler:
    minPageLimit = 1000

    def __init__(self, maxpageLevel: int, maxpagelimit: int):
        if maxpagelimit < SlaveAutoScaler.minPageLimit:
            maxpagelimit = SlaveAutoScaler.minPageLimit
        self.maxpageLevel = maxpageLevel
        self.maxpagelimit = maxpagelimit

    def get_optimal_capacity(self) -> int:
        mem_per_process = self.maxpagelimit * 50/1000  # normally it cost 0.005 MB per page
        total_mem = MachineInfo.get_memory()[0]
        return int(total_mem*0.7/mem_per_process)


class MiningRequestHandler(socketserver.StreamRequestHandler):
    def handle(self):
        self.send_and_receive()

    def send_and_receive(self):
        in_buffer = self.rfile
        out_buffer = self.wfile
        s = self.server.addtional_obj
        command = CommandProcessor.receive_command(in_buffer)
        #print("process cmd: ", command.cmd)
        if command is not None:
            reply = CommandStruct(cmd=ServerCommand.Com_ReplyOK)
            if command.cmd == ServerCommand.Com_Start:
                #print("start conversation:")
                CommandProcessor.send_command(out_buffer, reply)
            elif command.cmd == ServerCommand.Com_Stop_Mining:
                if s is not None and isinstance(s, SiteCheckProcessManager):
                    s.set_stop()
                CommandProcessor.send_command(out_buffer, reply)
            elif command.cmd == ServerCommand.Com_Setup:  # test this
                data = command.data
                if isinstance(data, SetupData):
                    cap2 = data.cap2
                    if cap2 == 0:
                        cap2 = SlaveAutoScaler(data.max_page_level, data.max_page_limit).get_optimal_capacity()
                    if isinstance(s, SiteCheckProcessManager):  # need to fix this
                        if s.is_alive():
                            s.set_stop()
                            s.join()
                    # elif isinstance(s, threading.Thread):
                    #     s.join(0)
                    print("init new process manager with para: ", data.get_serializable(False))
                    total_memory =MachineInfo.get_memory()[0]
                    mem_limit_per_crawler = int(total_memory * 0.8 / cap2)
                    if mem_limit_per_crawler >=  SiteCheckProcessManager.MEM_MINIMUM_REQ:
                        self.server.addtional_obj = SiteCheckProcessManager(data.ref, max_procss=cap2,
                                                                            concurrent_page=data.cap3,
                                                                            page_max_level=data.max_page_level,
                                                                            max_page_per_site=data.max_page_limit,
                                                                            memory_limit_per_process=mem_limit_per_crawler)
                        self.server.addtional_obj.start()
                    else:
                        reply.cmd = ServerCommand.Com_ReplyError
                        reply.data = "Not enough memory allocation for each crawler, must at least 100 Mb."
                CommandProcessor.send_command(out_buffer, reply)

            elif command.cmd == ServerCommand.Com_Clear_Cache:
                if isinstance(s, SiteCheckProcessManager):  # need to fix this
                    if s.is_alive():
                        s.set_stop()
                        s.join()
                    s.clear_cache()
                CommandProcessor.send_command(out_buffer, reply)

            elif command.cmd == ServerCommand.Com_Data:
                print("incoming data....")
                data = command.data
                if s is not None and isinstance(s, SiteCheckProcessManager):
                    if data.data is not None and len(data.data) > 0:
                        s.put_to_input_queue(data.data)
                else:
                    reply.cmd = ServerCommand.Com_ReplyError
                    reply.data = "something is wrong with data"
                CommandProcessor.send_command(out_buffer, reply)

            elif command.cmd == ServerCommand.Com_Get_Data:  # test this
                if s is not None and isinstance(s, SiteCheckProcessManager):
                    rawdata = []
                    if s.get_temp_result_count() > 0:
                        rawdata += [ScrapeDomainData(x.link, x.response_code) for x in s.get_temp_result_and_clear()
                                    if isinstance(x, OnSiteLink)]
                    #print("sending back:")
                    #print(rawdata)
                    if s.get_site_info_list_count() > 0:
                        rawdata += [info for info in s.get_site_info_list_and_clear()
                                    if isinstance(info, SeedSiteFeedback)]
                    data = MiningList(s.name, rawdata)
                    reply.data = data
                else:
                    reply.cmd = ServerCommand.Com_ReplyError
                    reply.data = "something is wrong with return data"
                CommandProcessor.send_command(out_buffer, reply)

            elif command.cmd == ServerCommand.Com_Status:
                #print("send back status!")
                CPU = MachineInfo.get_cpu(1)
                MEM = MachineInfo.get_memory()
                NET = MachineInfo.get_network(1)
                if s is not None and isinstance(s, SiteCheckProcessManager):
                    manager_state = s.get_state()
                    filter_progress = s.get_filter_progress()
                    status = ServerStatus(wait_job=manager_state.job_wait, done_job=manager_state.job_done,
                                          all_job=manager_state.job_all, total_page_done=manager_state.total_page_done,
                                          page_per_site=manager_state.average_page,
                                          result=manager_state.result_count, cpu_cores=CPU[0], cpu_percent=CPU[1],
                                          toal_memory=MEM[0], memory_percent=MEM[1], net_recieved=NET[0], net_send=NET[1],
                                          cap_slave=1, cap_process=s.max_prcess, cap_concurrent_page=s.concurrent_page,
                                          filter_done=filter_progress[0], filter_total=filter_progress[1])
                    reply.data = status
                else:
                    reply.cmd = ServerCommand.Com_ReplyError
                    reply.data = "something is wrong with the crawler."
                CommandProcessor.send_command(out_buffer, reply)

            elif command.cmd == ServerCommand.Com_Stop:
                #print("end conversation:")
                return
            else:
                reply.cmd = ServerCommand.Com_ReplyError
                reply.data = "command is not valid, please try again"
                CommandProcessor.send_command(out_buffer, reply)
            #print("finished cmd", command.cmd)
            self.send_and_receive()


def main(HOST=MiningTCPServer.DefaultListenAddr, PORT=MiningTCPServer.DefaultListenPort):
    addtional = SiteCheckProcessManager(max_procss=2)
    addtional.start()
    print("slave running at: " + HOST + " port: " + str(PORT))
    # Create the server, binding to localhost on port 9999
    server = MiningTCPServer((HOST, PORT), MiningRequestHandler, arg=addtional)
    server.serve_forever()

if __name__ == "__main__":
    main()

