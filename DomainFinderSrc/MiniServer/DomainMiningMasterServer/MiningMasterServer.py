import socketserver

from DomainFinderSrc.MiniServer.DomainMiningMasterServer.MiningControllers import *
from DomainFinderSrc.Utilities.MachineInfo import MachineInfo
from DomainFinderSrc.MiniServer.Common.MiningTCPServer import MiningTCPServer
from DomainFinderSrc.MiniServer.Common.SocketCommands import *
from DomainFinderSrc.MiniServer.DomainMiningMasterServer.AmazonControllers import *
from DomainFinderSrc.Utilities.Logging import ErrorLogger


class MasterRequestHandler(socketserver.StreamRequestHandler):
    def handle(self):
        self.send_and_receive()

    def add_slaves(self, s: MiningMasterController, data: SlaveOperationData):
        if data.slave_addrs is not None and len(data.slave_addrs) > 0:
            s.add_slaves(data.slave_addrs)
        elif data.ref != "" and data.count > 0:
            print("init from cloud")
            EC2 = EC2Controller("") # test this
            s.add_slaves(EC2.start_machines(data.ref, data.count))
        else:
            ErrorLogger.log_error("MasterRequestHandler.add_slaves()", ValueError("Add Slaves failed"))

    def remove_slaves(self, s: MiningMasterController, data: SlaveOperationData):
        if data.slave_addrs is not None and len(data.slave_addrs) > 0:
            s.remove_slaves(data.slave_addrs)
        elif data.ref != "" and data.count > 0:
            print("init from cloud")
            EC2 = EC2Controller("") # test this
            s.add_slaves(EC2.shut_down_machines(data.ref, data.count))
        else:
            ErrorLogger.log_error("MasterRequestHandler.remove_slaves()", ValueError("Remove Slaves failed"))

    def send_and_receive(self):
        in_buffer = self.rfile
        out_buffer = self.wfile
        s = self.server.addtional_obj
        command = CommandProcessor.receive_command(in_buffer)
        #print("process cmd: ", command.cmd)
        if command is not None and isinstance(s, MiningMasterController):
            reply = CommandStruct(cmd=ServerCommand.Com_ReplyOK)
            if command.cmd == ServerCommand.Com_Start:
                #print("start conversation:")
                CommandProcessor.send_command(out_buffer, reply)

            elif command.cmd == ServerCommand.Com_Stop:
                #print("end conversation:")
                return  # exit point

            elif command.cmd == ServerCommand.Com_Get_DB_DATA:
                data = command.data
                if isinstance(data, DBRequestFields):
                    try:
                        reply.data = s.get_db_results(db_type=data.db_type, db_name=data.db_name, index=data.index, length=data.length)
                    except Exception as ex:
                        ErrorLogger.log_error("MasterRequestHandler.send_and_receive()", ex,
                                              "cmd = ServerCommand.Com-Get-DB-DATA")
                        reply.cmd = ServerCommand.Com_ReplyError
                        reply.data = "Get DB data failed"
                else:
                    ErrorLogger.log_error("MasterRequestHandler.send_and_receive()",
                                          Exception("wrong data type recieved."), "cmd = ServerCommand.Com-Get-DB-DATA")
                    reply.cmd = ServerCommand.Com_ReplyError
                    reply.data = "Get DB data failed"
                CommandProcessor.send_command(out_buffer, reply)

            elif command.cmd == ServerCommand.Com_Remove_DB:
                data = command.data
                if isinstance(data, DBRequestFields):
                    try:
                        s.remove_db(db_type=data.db_type, db_name=data.db_name)
                    except Exception as ex:
                        ErrorLogger.log_error("MasterRequestHandler.send_and_receive()", ex,
                                              "cmd = ServerCommand.Com_DB-RM-DB")
                        reply.cmd = ServerCommand.Com_ReplyError
                        reply.data = "Remove DB failed"
                else:
                    ErrorLogger.log_error("MasterRequestHandler.send_and_receive()",
                                          Exception("wrong data type recieved."), "cmd = ServerCommand.Com_DB-RM-DB")
                    reply.cmd = ServerCommand.Com_ReplyError
                    reply.data = "Remove DB failed"
                CommandProcessor.send_command(out_buffer, reply)

            elif command.cmd == ServerCommand.Com_Setup:  # test this
                data = command.data
                try:
                    if s.is_alive():
                        s.stop()
                        s.join()
                    if isinstance(data, SetupData):
                        self.server.addtional_obj = MiningMasterController(ref=data.ref, cap_slave=data.cap,
                                                                           cap_slave_process=data.cap2,
                                                                           cap_concurrent_page=data.cap3,
                                                                           all_job=data.total,
                                                                           offset=data.offset,
                                                                           max_page_level=data.max_page_level,
                                                                           max_page_limit=data.max_page_limit,
                                                                           loopback_database=data.loopback,
                                                                           refresh_rate=data.refresh_rate,
                                                                           filters=data.db_filter)
                        if data.addtional_data is not None and isinstance(data.addtional_data, SlaveOperationData):
                            self.add_slaves(self.server.addtional_obj, data.addtional_data)
                            self.server.addtional_obj.setup_minging_slaves()
                        self.server.addtional_obj.start()
                    else:
                        raise NotImplementedError("other data type is not implemented.")
                except Exception as ex:
                    print(ex)
                    ErrorLogger.log_error("MasterRequestHandler.send_and_receive()", ex, "cmd = ServerCommand.Com_Setup()")
                    reply.cmd = ServerCommand.Com_ReplyError
                    reply.data = "Setup failed"
                CommandProcessor.send_command(out_buffer, reply)

            elif command.cmd == ServerCommand.Com_Clear_Cache:
                try:
                    if s.is_alive():
                        s.stop()
                        s.join()
                    s.clear_host_cache()
                    s.clear_slave_cache()
                except Exception as ex:
                    print(ex)
                    ErrorLogger.log_error("MasterRequestHandler.send_and_receive()", ex, "cmd = ServerCommand.Com_Clear_Cache()")
                    reply.cmd = ServerCommand.Com_ReplyError
                    reply.data = "Setup failed"
                CommandProcessor.send_command(out_buffer, reply)

            elif command.cmd == ServerCommand.Com_Add_Seed:
                data = command.data
                if isinstance(data, MiningList):
                    s.add_seeds(data)
                else:
                    reply.cmd = ServerCommand.Com_ReplyError
                    reply.data = "Add Seed Failed, format is wrong in server handler."
                CommandProcessor.send_command(out_buffer, reply)

            elif command.cmd == ServerCommand.Com_Add_Slave: # test this
                try:
                    data = command.data
                    if isinstance(data, SlaveOperationData):
                        self.add_slaves(s, data)
                    else:
                        raise NotImplementedError("other data type is not implemented.")
                except Exception as ex:
                    print(ex)
                    reply.cmd = ServerCommand.Com_ReplyError
                    reply.data = "Add slave failed"
                CommandProcessor.send_command(out_buffer, reply)

            elif command.cmd == ServerCommand.Com_Del_Slave: # test this
                try:
                    data = command.data
                    if isinstance(data, SlaveOperationData):
                        self.remove_slaves(s, data)
                    else:
                        raise NotImplementedError("other data type is not implemented.")
                except Exception as ex:
                    print(ex)
                    reply.cmd = ServerCommand.Com_ReplyError
                    reply.data = "Add slave failed"
                CommandProcessor.send_command(out_buffer, reply)

            elif command.cmd == ServerCommand.Com_Begin_Mining:  # not implemented, use setup to begin mining
                reply.cmd = ServerCommand.Com_ReplyError
                reply.data = "Add slave failed"

            elif command.cmd == ServerCommand.Com_Stop_Mining:  # test this
                try:
                    EC2 = EC2Controller("")
                    addrs = [slave.address.address for slave in s.slaves if isinstance(slave, Server)]
                    s.pause()
                    #s.slaves.clear()
                    #if s.isAlive:
                    #    s.join(0)
                    #self.server.addtional_obj = MiningMasterController()

                    EC2.shut_down_machines_list(addrs)
                except:
                    reply.cmd = ServerCommand.Com_ReplyError
                    reply.data = "Stop site failed"
                CommandProcessor.send_command(out_buffer, reply)

            elif command.cmd == ServerCommand.Com_Status:  # test this
                try:
                    CPU = MachineInfo.get_cpu(1)
                    MEM = MachineInfo.get_memory()
                    NET = MachineInfo.get_network(1)
                    slaveStatus = [slave.status for slave in s.slaves]
                    totalPage = sum([slave.total_page_done for slave in slaveStatus])
                    ave_page = 0
                    filter_progress = s.get_filter_progress()
                    if len(s.slaves) > 0:
                        ave_page = int(sum([slave.page_per_site for slave in slaveStatus])/len(s.slaves))
                    total_result = sum([slave.result for slave in slaveStatus])
                    total_cap_slave = sum([slave.cap_slave for slave in slaveStatus])
                    total_cap_process = sum([slave.cap_slave * slave.cap_process for slave in slaveStatus])
                    total_cap_page = sum([slave.cap_slave * slave.cap_process * slave.cap_concurrent_page for slave in slaveStatus])
                    status = ServerStatus(wait_job=s.job_all - s.job_done, done_job=s.job_done, all_job=s.job_all,
                                          total_page_done=totalPage, page_per_site=ave_page,
                                          result=total_result, cpu_cores=CPU[0], cpu_percent=CPU[1],
                                          toal_memory=MEM[0], memory_percent=MEM[1], net_recieved=NET[0], net_send=NET[1],
                                          cap_slave=total_cap_slave, cap_process= total_cap_process, cap_concurrent_page= total_cap_page,
                                          filter_done=filter_progress[0], filter_total=filter_progress[1])
                    server = Server(server_type=ServerType.ty_Host, status=status, address=ServerAddress("localhost", MiningTCPServer.DefaultListenPort))
                    servers = []
                    servers.append(server)
                    servers += s.slaves
                    reply.data = MiningList(s.ref, servers)
                except:
                    reply.cmd = ServerCommand.Com_ReplyError
                    reply.data = "getting status failed"
                CommandProcessor.send_command(out_buffer, reply)

            elif command.cmd == ServerCommand.Com_DataBase_Status:  # test this
                reply.data = s.get_db_stats()  # send back a copy
                CommandProcessor.send_command(out_buffer, reply)

            elif command.cmd == ServerCommand.Com_Set_DB_Filter:
                data = command.data
                if isinstance(data, DBFilterCollection):
                    if data != s.filter_shadow:
                        s.filter_shadow = data
                        s.update_db_stats(True)
                else:
                    reply.cmd =ServerCommand.Com_ReplyError
                    reply.data = "wrong data type for filters, should be DBFilterCollection"
                CommandProcessor.send_command(out_buffer, reply)

            elif command.cmd == ServerCommand.Com_Progress: # this this
                reply.data = PrograssData(ref=s.ref, done=s.job_done, all_job=s.job_all,offset=s.offset,
                                          duration=s.end_time - s.start_time, in_progress=s.in_progress)
                CommandProcessor.send_command(out_buffer, reply)

            else:
                reply.cmd = ServerCommand.Com_ReplyError
                reply.data = "command is not valid, please try again"
                CommandProcessor.send_command(out_buffer, reply)

            #CommandProcessor.send_command(out_buffer, reply)
            #print("finished cmd ", command.cmd)
            self.send_and_receive()  # recursive to make a conversation


def main(HOST=MiningTCPServer.DefaultListenAddr, PORT=MiningTCPServer.DefaultListenPort):
    addtional = MiningMasterController()
    addtional.start()
    print("host running at: " + HOST + " port: " + str(PORT))
    # Create the server, binding to localhost on port 9999
    server = MiningTCPServer((HOST, PORT), MasterRequestHandler, arg=addtional)
    server.serve_forever()

if __name__ == "__main__":
    main()

