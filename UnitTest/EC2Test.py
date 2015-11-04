from DomainFinderSrc.AmazonServiceCom import Const, EC2Resource
from unittest import TestCase
from boto3.ec2 import *
import boto3
import inspect
from UnitTest.Accounts import SiteAccount, amazon_ec2_account
from DomainFinderSrc.AmazonServiceCom.ResCommon import ServiceUtility
import time
from threading import Event
from DomainFinderSrc.AmazonServiceCom.DataStruct import *


class EC2Test(TestCase):
    def testTerminateWithTimeout(self):
        tag_name = "LaunchGroupCrawl"
        tag_value = "TestCrawl"
        timeout_min = 60
        counter = 0
        results = EC2Resource.EC2Resource.get_instances_by_tag(amazon_ec2_account, zone=Const.Zone.US_West_2A,
                                                                tag_key=tag_name, tag_value=tag_value)
        id_list = []
        if results is not None:
            print("here is a list of ip we can use:")
            for item in results:
                print(item.ins_id)
                id_list.append(item.ins_id)
        if len(id_list) > 0:
            print("everything is ok")
            while counter < timeout_min:
                time.sleep(60)
                counter += 1
                print("sleep ", counter)
            EC2Resource.EC2Resource.terminate_instances(amazon_ec2_account, zone=Const.Zone.US_West_2A,
                                                        instance_ids=id_list)

    def testEC2_create(self):
        para = {"region_name": "us-west-1"}
        boto3.setup_default_session(**para)
        ec2_s = boto3.resource('ec2')
        class_name = ec2_s.__class__
        print(class_name)
        file = inspect.getfile(class_name)
        print(file)
        methods = [getattr(ec2_s, method) for method in dir(ec2_s) if callable(getattr(ec2_s, method)) and "__" not in str(method)]
        for method in methods:
            print(method, " args: ", inspect.getargspec(method))
        print(ec2_s.Subnet)

    def testCommonParamters(self):
        action = "DescribeJobFlows"
        test_account = SiteAccount(siteType=7, userID="test",
                                   AccessID=amazon_ec2_account.AccessID, APIkey=amazon_ec2_account.APIKey)
        parameters = ServiceUtility.get_common_request_query(Const.EndPoint.EC2, False, action, test_account.AccessID,
                                                                         test_account.APIKey, {}, )
        print(parameters)

    def testSpotInstanceRequestSpot(self): # pass
        request = EC2Resource.EC2Resource.request_spot_instances(amazon_ec2_account, image_id=Const.ImageId.Crawler_v1047,
                                                      key_name=Const.SshSecureKeyName.Default,
                                                      security_group=Const.SecureGroupId.CrawlOperation,
                                                      instance_type=Const.Ec2InstanceType.M4_Large,
                                                      zone=Const.Zone.US_West_2A,
                                                      instance_count=2,
                                                      price=0.1,
                                                      launch_group="TestRun",
                                                      dry_run=False)
        request_ids = request.ids
        print(request)
        for item in request_ids:
            print(item)

    def testSpotInstanceDescription(self): # pass
        results =EC2Resource.EC2Resource.get_spot_instances_info(amazon_ec2_account, zone=Const.Zone.US_West_2A,
                                                                 launch_group="TestRun")
                                                                # request_id="sir-037wfexg")
        request_ip_list = []
        instance_ip_list = []
        for item in results:
            request_ip_list.append(item.request_id)
            instance_ip_list.append(item.ins_id)
            print(item)
        print("request_ip_list", request_ip_list)
        print("instance_ip_list", instance_ip_list)

    def testConcelSpotInstances(self):
        request_ids = ["sir-037ves6e", "sir-0383fztq"]
        results, success = EC2Resource.EC2Resource.cancel_spot_instances(amazon_ec2_account, zone=Const.Zone.US_West_2A, request_ids=request_ids)
        print("results are:", success)
        for item in results:
            print(item)

    def testTerminateInstances(self):
        instance_ids = ['i-ef2f9d2b', 'i-a22e9c66']
        EC2Resource.EC2Resource.terminate_instances(amazon_ec2_account, zone=Const.Zone.US_West_2A,
                                                    instance_ids=instance_ids)

    def testAddTag(self):
        instance_ids = ['i-76714bb3', 'i-6f5aa3a6']
        tag_dict = {"LaunchGroup": "Test"}
        result = EC2Resource.EC2Resource.adding_tag_to_instances(amazon_ec2_account,
                                                                  zone=Const.Zone.US_West_2A, ids=instance_ids,
                                                                  tags_dict=tag_dict)
        print(result)

    def testGetInstanceByTag(self):
        tag_name = "LaunchGroupCrawl"
        tag_value = "TestCrawl"
        results = EC2Resource.EC2Resource.get_instances_by_tag(amazon_ec2_account, zone=Const.Zone.US_West_2A,
                                                                tag_key=tag_name, tag_value=tag_value)
        for item in results:
            if isinstance(item, InstanceInfo):
                print(item.private_ip)

    def testAutomationFlow1(self):
        tag_name = "LaunchGroupCrawl"
        tag_value = "TestCrawl"
        tag_dict = {tag_name: tag_value}
        instance_count = 20
        mins_to_wait = 30
        min_count = 0
        instance_type = Const.Ec2InstanceType.M4_4X
        instance_max_price = 1.1
        # request = EC2Resource.EC2Resource.request_spot_instances(amazon_ec2_account,
        #                                                          image_id=Const.ImageId.Crawler_v1047,
        #                                                          key_name=Const.SshSecureKeyName.Default,
        #                                                          security_group=Const.SecureGroupId.CrawlOperation,
        #                                                          instance_type=instance_type,
        #                                                          zone=Const.Zone.US_West_2A,
        #                                                          instance_count=instance_count,
        #                                                          price=instance_max_price,
        #                                                          launch_group=tag_value,
        #                                                          request_valid_duration_min= mins_to_wait,
        #                                                          dry_run=False)
        # request_ids = request.ids
        # print("request is send, request ids are:")
        # if request_ids is not None:
        #     for item in request_ids:
        #         print(item)
        # time.sleep(1)

        request_id_list = []
        instance_id_list = []
        stop_event = Event()
        while not stop_event.is_set() or min_count < mins_to_wait:
            results =EC2Resource.EC2Resource.get_spot_instances_info(amazon_ec2_account, zone=Const.Zone.US_West_2A,
                                                                     launch_group=tag_value)

            if results is not None:
                for item in results:
                    if item.ins_id is not None and len(item.ins_id) > 0:
                        request_id_list.append(item.request_id)
                        instance_id_list.append(item.ins_id)
                        print(item)
                # print("request_ip_list", request_id_list)
                # print("instance_ip_list", instance_id_list)
                if len(instance_id_list) > 0:
                    print("instance finally launched!")
                    result = EC2Resource.EC2Resource.adding_tag_to_instances(amazon_ec2_account,
                                                                              zone=Const.Zone.US_West_2A,
                                                                              ids=instance_id_list,
                                                                              tags_dict=tag_dict)
                    print("adding launch group tag:", result)
                    break
            print("nothing happens yet, please wait")
            time.sleep(60)
            min_count += 1

        private_ip_list = []
        if len(instance_id_list) > 0:
            results = EC2Resource.EC2Resource.get_instances_by_tag(amazon_ec2_account, zone=Const.Zone.US_West_2A,
                                                                    tag_key=tag_name, tag_value=tag_value)
            if results is not None:
                print("here is a list of ip we can use:")
                for item in results:
                    print(item)
                    private_ip_list.append(item.private_ip)
        if len(private_ip_list) > 0:
            print("everything is ok")


