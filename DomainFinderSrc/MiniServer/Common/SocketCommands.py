import json

from DomainFinderSrc.Utilities.Serializable import Serializable


class ServerCommand:
    Com_Start = "START" # Accept All
    Com_Stop = "STOP" # Accept All
    Com_ReplyOK = "OK" # Reply command is OK, Accept All
    Com_ReplyError = "ERROR" #indicate the request has error, Accept All
    Com_Status = "STATUS" #server send this command to slave to response of slave's status
    Com_Data = "DATA" #send DATA command to initiate data transfer, Accept Slave
    Com_Setup = "SETUP" # Accept Slave
    Com_Get_Data = "GET-DATA"
    Com_DataBase_Status = "DB-STATUS" #Accept Database
    Com_Begin_Mining = "MINE-START"
    Com_Stop_Mining = "MINE-STOP"
    Com_Add_Slave ="SLAVE-ADD"  # add slaves
    Com_Del_Slave = "SlAVE-DEL"  # delete slaves
    Com_Progress = "PROGRASS"
    Com_Set_DB_Filter = "DB-FILTER-SET"  # Accept by Host
    Com_Get_DB_Filter = "DB-FILTER-GET"  # Accept by Host
    Com_Add_Seed = "DB-ADD-SEED"
    Com_Remove_DB = "DB-RM-DB"  # remove a database
    Com_Get_DB_DATA = "DB-GET-DB-DATA"
    Com_Get_Proxes = "GET-PROXY"
    Com_Set_Proxes = "SET-PROXY"
    Com_Clear_Cache = "CLEAR-CACHE"


class ServerState:
    State_Active = "ACTIVE"
    State_Idle = "IDLE"
    State_Init = "INIT"


class DBRequestFields(Serializable):
    def __init__(self, db_name: str="", db_type: str="", index: int=0, length: int=0):
        self.db_name = db_name
        self.db_type = db_type
        self.index = index
        self.length = length


class MiningList(Serializable):
    """
    A genral data structure to pass data between master and slaves, type(data) varies depending on scenarios
    """
    def __init__(self, ref: str="", data: []=None):
        """
        :param ref: ref in str
        :param data: data type must be Serializable & isinstance(array)
        :return:
        """
        self.ref = ref
        self.data = data


class SlaveOperationData(Serializable):
    """
    A data structure to pass slave addrs between Webserver and master
    """
    def __init__(self, ref: str="", count: int=0, slaves_addrs: []=None):
        """
        Pass this data type to MiningMasterServer
        :param ref: The reference of the slave type
        :param count: number of slaves
        :param slaves_addrs: slaves' address, if is None the MiningMasterServer will opearte on random addr with count
        :return:
        """
        self.ref = ref
        self.count = count
        self.slave_addrs = slaves_addrs


class SetupData(Serializable):
    def __init__(self, ref: str="", cap: int=0, cap2: int=0, cap3=0, total: int=0, offset: int=0, max_page_level: int=0, max_page_limit: int=0,
                 loopback=True, refresh_rate=30, company="", company_code="", db_filter: Serializable=None, addtional_data: Serializable=None):
        self.ref = ref
        self.cap = cap  # master: number of slves
        self.cap2 = cap2  # master, slave: number of process
        self.cap3 = cap3  # master, slave: number of concurrent page
        self.total = total
        self.offset = offset
        self.max_page_level = max_page_level
        self.max_page_limit = max_page_limit
        self.loopback = loopback
        self.refresh_rate = refresh_rate

        self.company = company
        self.company_code = company_code
        self.db_filter = db_filter
        self.addtional_data = addtional_data


class SeedSiteFeedback(Serializable):
    def __init__(self, domain: str="", page_count: int=0):
        self.domain = domain
        self.page_count = page_count


class PrograssData(Serializable):
    def __init__(self,ref="", done: int=0, all_job: int=0, offset=0, duration: float=0.0, in_progress=False):
        self.done = done
        self.all = all_job
        self.duration = duration  # in second
        self.in_progress = in_progress
        self.ref = ref
        self.offset = offset


class SignalData(Serializable):
    def __init__(self, data=None):
        self.data = data


class DatabaseStatus(Serializable):
    def __init__(self, name: str="", seeds: int=0, results: int=0, filtered: int=0):
        """
        hold the general info of a database
        :param name: name of a database
        :param seeds:  number of seed sites
        :param results: number of results from seed list, all the external sites.
        :param filtered: number of expired domains that has good matrix, selected from results
        :return:
        """
        self.name = name
        self.seeds = seeds
        self.results = results
        self.filtered = filtered

    def __str__(self):
        return self.name + " seed: " + str(self.seeds) + " results: " + str(self.results) + " filtered: " + str(self.filtered)


class ServerStatus(Serializable):
    def __init__(self, wait_job: int=0, done_job: int=0, all_job: int=0, total_page_done: int=0, page_per_site: int=0,
                 result: int=0, cpu_cores: int=0, cpu_percent: float=0.0, toal_memory: float=0.0,
                 memory_percent: float=0.0, net_recieved: float=0.0, net_send: float=0.0,cap_slave = 0, cap_process: int=0,
                 cap_concurrent_page=0, page_per_s= 0, filter_total=0, filter_done=0):
        self.wait_job = wait_job  # the job wait in the queue
        self.done_job = done_job  # the job finished
        self.all_job = all_job  # the job in processing
        self.total_page_done = total_page_done  # number of pages crawled
        self.page_per_sec = page_per_s
        self.page_per_site = page_per_site  # number of pages processed per second
        self.result = result  # number of results in crawler

        self.cpu_cores = cpu_cores  # number of CPU cores
        self.cpu_percent = cpu_percent  # percentage CPU used
        self.memory = toal_memory  # total memory of the machine
        self.memory_percent = memory_percent  # memory used as percentage
        self.net_recieved = net_recieved  # data recieved in MB/s
        self.net_send = net_send  # data send in MB/s

        self.cap_slave = cap_slave
        self.cap_process = cap_process  # indicate how many pages can run in parallel
        self.cap_concurrent_page = cap_concurrent_page

        self.filter_total = filter_total
        self.filter_done = filter_done

    def __str__(self):
        return str(self.__dict__)


class ServerAddress(Serializable):
    def __init__(self, address: str="0.0.0.0", port: int=0):
        self.address = address
        self.port = port

    def __str__(self):
        return self.address + ":" + str(self.port)


class ServerType:
    ty_Host = 1
    ty_MiningSlaveSmall = 2
    ty_Database = 5

    @staticmethod
    def to_str(type_int: int):
        if type_int == ServerType.ty_Host:
            return "Host"
        elif type_int == ServerType.ty_MiningSlaveSmall:
            return "Miner"
        elif type_int == ServerType.ty_Database:
            return "Database"
        else:
            return "Unknown"


class Server(Serializable):
    def __init__(self, server_type: int=ServerType.ty_Host, status=ServerStatus(), address=ServerAddress()):
        self.type = ServerType.to_str(server_type)
        self.status = status
        self.address = address

    def __str__(self):
        return str(self.address) + " " + self.type


class CommandStruct(Serializable):
    def __init__(self, cmd: str="", data: Serializable=None):#, incoming_server=ServerAddress()):
        self.cmd = cmd
        self.data = data
        #self.server = incoming_server


class CommandProcessor:
    def __init__(self, in_buf, out_buf):
        self.in_buf = in_buf
        self.out_buf = out_buf

    @staticmethod
    def parse_command(command: str) ->CommandStruct:
        j = json.loads(command)
        return Serializable.get_deserialized(j)

    @staticmethod
    def make_command(command: CommandStruct)->str:
        j = json.dumps(command.get_serializable(), ensure_ascii=True)
        return j

    @staticmethod
    def send_command(out_buffer, command: CommandStruct):
        if out_buffer is not None:
            j = CommandProcessor.make_command(command)
            out_buffer.write(bytes(j + "\r\n", "utf-8"))

    def send_command_ex(self, command: CommandStruct):
        CommandProcessor.send_command(self.out_buf, command)

    @staticmethod
    def receive_command(in_buffer) -> CommandStruct:
        if in_buffer is not None:
            j = in_buffer.readline().strip()
            return CommandProcessor.parse_command((str(j, encoding="utf-8")))
        else:
            return None

    def receive_command_ex(self):
        return CommandProcessor.receive_command(self.in_buf)

    @staticmethod
    def check_response(command: CommandStruct, in_buf, out_buf, key_to_check: str=ServerCommand.Com_ReplyOK) -> (True, CommandStruct):
        CommandProcessor.send_command(out_buf, command)
        response = CommandProcessor.receive_command(in_buf)
        if response.cmd == key_to_check:
            return True, response
        else:
            return False, response

    def check_response_ex(self, command: CommandStruct, key_to_check: str=ServerCommand.Com_ReplyOK) -> (True, CommandStruct):
        return CommandProcessor.check_response(command, self.in_buf, self.out_buf, key_to_check)

    @staticmethod
    def check_chain_responses(command_list: [], in_buf, out_buf, key_to_check: str=ServerCommand.Com_ReplyOK) -> True:
        everything_ok = True
        response = None
        for command in command_list:
            response = CommandProcessor.check_response(command, in_buf, out_buf, key_to_check)
            if response is None or response[0]:
                everything_ok = False
        return everything_ok

    def check_chain_responses_ex(self, command_list: [], key_to_check: str=ServerCommand.Com_ReplyOK) -> True:
        return CommandProcessor.check_chain_responses(command_list,self.in_buf, self.out_buf, key_to_check)
