from threading import Thread, Event, RLock
import time
from DomainFinderSrc.Utilities.Serializable import Serializable
from DomainFinderSrc.SiteConst import AccountType, AccountManager, SiteAccount
from copy import deepcopy
from DomainFinderSrc.AmazonServiceCom import Const
from DomainFinderSrc.AmazonServiceCom import EC2Resource
from DomainFinderSrc.MiniServer.Common.AbstractServer import ServerRequestHandler
from DomainFinderSrc.MiniServer.Common.SocketCommands import CommandStruct, Server, ServerCommand, ServerType, MiningList, ServerAddress
from DomainFinderSrc.MiniServer.DatabaseServer.CategorySiteDB import SeedDBRequest
from DomainFinderSrc.MiniServer.DomainMiningMasterServer.HostController import HostController
from DomainFinderSrc.MiniServer.Common.MiningTCPServer import MiningTCPServer

class CrawlTask(Serializable):
    def __init__(self, unique_ref="", host_addr="", db_addr="", slave_count=10,
                 instance_id="", duration_hour=2, niches=[], seed_per_niche=10000, init_seeds=[]):
        """
        instance_id: type of Ec2InstanceType
        """
        self.unique_ref = unique_ref
        self.host_addr, self.db_addr = host_addr, db_addr
        self.slave_addrs, self.slave_count, self.instance_id = [], slave_count, instance_id
        self.duration_hour, self.niches, self.seed_per_niche = duration_hour, niches, seed_per_niche
        self.init_seeds = init_seeds
        self.is_running = False


class CrawlTaskController(ServerRequestHandler):
    """
    TODO: complete the following functions.
    """
    def __init__(self, stop_event: Event, parent: ServerRequestHandler,  account_db_addr: str="", seed_source_addr=""):
        """
        :param stop_event:
        :param account_db_addr:
        :param seed_source: you have to either provide seed_source or seed_source_addr, this could be a list of sites or
        :param seed_source_addr: ip addr of the seed source db
        :return:
        """
        self._stop_event = stop_event
        self._account_manager = AccountManager(account_db_addr)
        self._moz_account_list = [x for x in self._account_manager.AccountList if x.siteType == AccountType.Moz]
        self._majestic_account = self._account_manager.get_accounts(AccountType.Majestic)[0]
        self._amazon_ec2_account = self._account_manager.get_accounts(AccountType.AmazonEC2)[0]
        self._account_lock = RLock()
        self._task_lock = RLock()
        self._task_list = []
        self._parent_server = parent
        self._seed_source_addr = seed_source_addr
        ServerRequestHandler.__init__(self)

    def add_task(self, task: CrawlTask):
        pass

    def remove_task(self, task: CrawlTask):
        pass

    def _get_moz_account(self, count: int):
        accounts = []
        with self._account_lock:
            available_accs = [x for x in self._moz_account_list if x.Available]
            if len(available_accs) >= count:
                accounts = available_accs[0: count]
                for item in accounts:
                    if isinstance(item, SiteAccount):
                        accounts.append(deepcopy(item))
                        item.Available = False
        return accounts

    @staticmethod
    def request_spot_instances(amazon_ec2_account: SiteAccount, image_id: str,
                                   instance_type: str, zone: str, instance_count: int,
                                   max_price: float, tag_ref: str, stop_event: Event, return_results: list):
        tag_name = "LaunchGroupCrawl"
        tag_value = tag_ref
        tag_dict = {tag_name: tag_value}
        mins_to_wait = 30
        min_count = 0
        instance_type = instance_type
        instance_max_price = max_price
        zone = zone
        request_id_list = []
        request = EC2Resource.EC2Resource.request_spot_instances(amazon_ec2_account,
                                                                 # image_id=Const.ImageId.Crawler_v1047,
                                                                 image_id=image_id,
                                                                 key_name=Const.SshSecureKeyName.Default,
                                                                 security_group=Const.SecureGroupId.CrawlOperation,
                                                                 instance_type=instance_type,
                                                                 zone=zone,
                                                                 instance_count=instance_count,
                                                                 price=instance_max_price,
                                                                 launch_group=tag_value,
                                                                 request_valid_duration_min= mins_to_wait,
                                                                 dry_run=False)
        request_ids = request.ids
        print("request is send, request ids are:")
        if request_ids is not None:
            for item in request_ids:
                print(item)
        time.sleep(1)

        instance_id_list = []
        while min_count < mins_to_wait:
            if stop_event.is_set():
                EC2Resource.EC2Resource.cancel_spot_instances(amazon_ec2_account, zone=zone, request_ids=request_id_list)
                break

            results =EC2Resource.EC2Resource.get_spot_instances_info(amazon_ec2_account, zone=zone,
                                                                     launch_group=tag_value)

            if results is not None:
                for item in results:
                    if item.ins_id is not None and len(item.ins_id) > 0:
                        # request_id_list.append(item.request_id)
                        instance_id_list.append(item.ins_id)
                        print(item)
                if len(instance_id_list) > 0:
                    print("instance finally launched!")
                    result = EC2Resource.EC2Resource.adding_tag_to_instances(amazon_ec2_account,
                                                                              zone=zone,
                                                                              ids=instance_id_list,
                                                                              tags_dict=tag_dict)
                    print("adding launch group tag:", result)
                    break
            print("nothing happens yet, please wait")
            time.sleep(60)
            min_count += 1

        private_ip_list = []
        if len(instance_id_list) > 0:
            while not stop_event.is_set():
                results = EC2Resource.EC2Resource.get_instances_by_tag(amazon_ec2_account, zone=zone,
                                                                        tag_key=tag_name, tag_value=tag_value)
                if results is not None:
                    print("here is a list of ip we can use:")
                    if results[0].state == Const.InstanceState.Running:
                        for item in results:
                            return_results.append(item.private_ip)
                            print(item.private_ip)
                            private_ip_list.append(item.private_ip)

                        break
                time.sleep(60)
        if len(private_ip_list) > 0:
            return private_ip_list
        else:
            return []

    @staticmethod
    def upload_seeds(ref: str, target_host: Server, seed_server: ServerRequestHandler, niches=[], init_seeds=[],
                     seed_source_addr="", seeds_per_niche=5000):
        seeds = init_seeds
        if len(seeds) == 0:
            if len(seed_source_addr) > 0:
                raise NotImplementedError
            else:
                for niche in niches:
                    request = SeedDBRequest(niche=niche, random_read=True, reverse_read=True,
                                            data_len=seeds_per_niche)
                    cmd = CommandStruct(cmd=ServerCommand.Com_Get_DB_DATA,
                                        target=ServerType.ty_Seed_Database, data=request)

                    if isinstance(seed_server, ServerRequestHandler):
                        # case when it is a local seed db
                        temp = seed_server.handle_request(cmd)
                    elif len(seed_source_addr) > 0:
                        # TODO: case when it is a remote seed db
                        temp = None
                    else:
                        raise NotImplementedError

                    if isinstance(temp, MiningList):
                        seeds += temp.data

        seeds = [x for x in set(seeds)]
        in_data = MiningList(ref=ref, data=seeds)
        hostController = HostController(target_host, cmd=ServerCommand.Com_Add_Seed, in_data=in_data)
        hostController.start()
        hostController.join()
        return len(seeds)

    def _run_task(self, task: CrawlTask):
        moz_account_count = 750
        accounts = self._get_moz_account(moz_account_count)
        zone = Const.Zone.US_West_2A
        image_id = Const.ImageId.Crawler_v1050

        if len(accounts) > 0:
            host_type = Const.Ec2InstanceType.T2_Micro
            host_price = 0.2
            if task.instance_id == Const.Ec2InstanceType.M4_Large:
                slave_count = 160
                max_price = 1.1
            elif task.instance_id == Const.Ec2InstanceType.M4_4X:
                slave_count = 20
                max_price = 0.15
            else:
                raise ValueError("CrawlTaskController._run_task: invalid CrawlTask.instance_id")

            host_ref = task.unique_ref+"Host"
            slave_results = list()
            slave_request_t = Thread(target=CrawlTaskController.request_spot_instances,
                                     args=(self._amazon_ec2_account, image_id, task.instance_id,
                                           zone, slave_count, max_price, task.unique_ref,
                                           self._stop_event, slave_results))
            host_results = list()
            host_ip = task.host_addr
            host_request_t = Thread(target=CrawlTaskController)
            host_request_t = Thread(target=CrawlTaskController.request_spot_instances,
                                     args=(self._amazon_ec2_account, image_id, host_type,
                                           zone, 1, host_price, host_ref,
                                           self._stop_event, host_results))
            slave_request_t.start()
            if len(host_ip) == 0:
                host_request_t.start()
            if slave_request_t.is_alive():
                slave_request_t.join()
            if host_request_t.is_alive():
                host_request_t.join()
            if len(host_results) == 0:
                # todo: should start the instance normally, and add the tag
                raise NotImplementedError
            # upload seeds
            seeds_count = self.upload_seeds(task.unique_ref,
                              target_host=Server(address=ServerAddress(task.host_addr,MiningTCPServer.DefaultListenPort)),
                              seed_server=self._parent_server, niches=task.niches, init_seeds=task.init_seeds,
                              seed_source_addr=self._seed_source_addr, seeds_per_niche=task.seed_per_niche)
            # todo...



    def update_running_task_status(self):
        pass


    def handle_request(self, cmd: CommandStruct):
        raise NotImplementedError

    def run(self):
        while not self._stop_event.is_set():
            self.update_running_task_status()
            time.sleep(1)
