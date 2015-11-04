from DomainFinderSrc.SiteConst import SiteAccount
from .Const import *
from .ResCommon import ServiceUtility
import datetime
from .DataStruct import *


class EC2Resource:

    @staticmethod
    def request_spot_instances(account: SiteAccount, image_id: str, key_name: str, security_group: str,
                               instance_type: str, zone: str, instance_count: int, price: float,
                               hour_duration=-1, launch_group='', request_valid_duration_min=30,
                               dry_run=False) -> SpotRequestInfo:

        time_delay = datetime.datetime.utcnow() + datetime.timedelta(minutes=request_valid_duration_min)
        parameters = {
            "SpotPrice": "{0:.2f}".format(price,),
            "InstanceCount": instance_count,
            "Type": "one-time",
            "LaunchSpecification.ImageId": image_id,
            "LaunchSpecification.KeyName": key_name,
            "LaunchSpecification.SecurityGroupId.1": security_group,
            "LaunchSpecification.InstanceType": instance_type,
            # "LaunchSpecification.SubnetId": subnet,
            "LaunchSpecification.Placement.AvailabilityZone": zone,
            # "BlockDurationMinutes": hour_duration * 60,
            "ValidUntil": str(time_delay.strftime("%Y-%m-%dT%H:%M:%S")),
        }
        if len(launch_group) > 0:
            assert hour_duration < 0, "cannot specify individual termination if launch together"
            parameters.update({"LaunchGroup": launch_group})
        if hour_duration > 0:
            parameters.update({"BlockDurationMinutes": hour_duration * 60})
        try:
            element = ServiceUtility.make_request(account, EndPoint.EC2, zone, "RequestSpotInstances",
                                                  dry_run, parameters, use_https=True)
            name_space, tag = ServiceUtility.get_tag_uri_and_name(element)
            spotInstanceRequestSet_item = element[1][0]
            request_id = element[0].text
            state = spotInstanceRequestSet_item[3].text
            status = spotInstanceRequestSet_item[4]
            status_code = status[0].text
            target_tag = "{{{0:s}}}spotInstanceRequestId".format(name_space,)
            request_ids = [item.text for item in element.iter(target_tag)]
            info = SpotRequestInfo()
            info.req_id, info.state, info.status, info.instance_ids = request_id, state, status_code, request_ids
            return info
        except Exception as ex:
            print(ex)
            return None

    @staticmethod
    def cancel_spot_instances(account: SiteAccount, zone: str, request_ids: [],
                              target_states=[SpotInstanceState.Cancelled, SpotInstanceState.Closed],
                              dry_run=False) -> ([], bool):
        """
        cancel spot instances by a list of request ids
        :param account:
        :param zone:
        :param request_ids:
        :param target_states: desired state you instance been cancelled, of type SpotInstanceState
        :param dry_run:
        :return: tuple(a list of CancelledSpotInstanceResponse, True if all instances has met the target_states)
        """
        parameters = {
        }
        counter = 1
        for item in request_ids:
            if isinstance(item, str):
                parameters.update({"SpotInstanceRequestId.{0:d}".format(counter,): item})
                counter += 1
        info = []
        try:
            element = ServiceUtility.make_request(account, EndPoint.EC2, zone, "CancelSpotInstanceRequests",
                                                  dry_run, parameters, use_https=True)
            name_space, tag = ServiceUtility.get_tag_uri_and_name(element)
            spotInstanceRequestSet = element[1]
            target_tag = "{{{0:s}}}item".format(name_space,)
            all_state_valid = True
            for item in spotInstanceRequestSet.findall(target_tag):
                item_state = ServiceUtility.get_tag_content("state", item, name_space)
                request_id = ServiceUtility.get_tag_content("spotInstanceRequestId", item, name_space)
                request = CancelledSpotInstanceResponse()
                request.state = item_state
                request.req_id = request_id
                if item_state not in target_states:
                    all_state_valid = False
                info.append(request)
            return info, all_state_valid
            # spotInstanceRequestSet_item = element[1][0]
            # request_id = spotInstanceRequestSet_item[0].text
        except Exception as ex:
            print(ex)
            return info, False

    @staticmethod
    def get_spot_instances_info(account: SiteAccount, zone: str, request_id="", launch_group="", dry_run=False):
        counter = 1
        parameters = {}
        if len(request_id) > 0:
            parameters.update({"Filter.{0:d}.Name".format(counter): "spot-instance-request-id",
                               "Filter.{0:d}.Value.1".format(counter): request_id})
            counter += 1
        if len(launch_group) > 0:
            parameters.update({"Filter.{0:d}.Name".format(counter): "launch-group",
                               "Filter.{0:d}.Value.1".format(counter): launch_group})
            counter += 1
        print(parameters)
        try:
            element = ServiceUtility.make_request(account, EndPoint.EC2, zone, "DescribeSpotInstanceRequests",
                                                  dry_run, parameters, use_https=True)
            name_space, tag = ServiceUtility.get_tag_uri_and_name(element)
            spotInstanceRequestSet = element[1]
            info = []
            target_tag = "{{{0:s}}}item".format(name_space,)
            for item in spotInstanceRequestSet.findall(target_tag):
                item_request_id = item.find("{{{0:s}}}spotInstanceRequestId".format(name_space,)).text
                item_state = ServiceUtility.get_tag_content("state", item, name_space)
                item_status = item.find("{{{0:s}}}status".format(name_space,))[0].text
                lauch_spec = item.find("{{{0:s}}}launchSpecification".format(name_space,))
                item_type = lauch_spec.find("{{{0:s}}}instanceType".format(name_space,)).text
                item_instance_id_tag = item.find("{{{0:s}}}instanceId".format(name_space,))
                if item_instance_id_tag is not None:
                    item_instance_id = item_instance_id_tag.text
                else:
                    item_instance_id = ""
                create_time_tag = item.find("{{{0:s}}}createTime".format(name_space,))
                create_time = ""
                if create_time_tag is not None:
                    create_time = create_time_tag.text
                temp = InstanceInfo()
                temp.ins_type = item_type
                temp.request_id = item_request_id
                temp.ins_id = item_instance_id
                temp.status_code = item_status
                temp.state = item_state
                temp.launch_time = create_time
                info.append(temp)
            return info
        except Exception as ex:
            print(ex)
            return None

    @staticmethod
    def adding_tag_to_instances(account: SiteAccount, zone: str, ids: [], tags_dict: dict, dry_run=False) -> bool:
        """
        http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_CreateTags.html
        :param account:
        :param ids: could be instance id or ami id
        :param tag_name: name of the tag
        :param tag_value: value of the tag
        :param dry_run:
        :return:
        """
        counter = 1
        parameters = {}
        for k, v in tags_dict.items():
            parameters.update({
                "Tag.{0:d}.Key".format(counter,): k,
                "Tag.{0:d}.Value".format(counter,): str(v)})
            counter += 1

        counter = 1
        for item in ids:
            parameters.update({"ResourceId.{0:d}".format(counter,): item})
            counter += 1

        try:
            element = ServiceUtility.make_request(account, EndPoint.EC2, zone, "CreateTags",
                                                  dry_run, parameters, use_https=True)
            name_space, tag = ServiceUtility.get_tag_uri_and_name(element)
            return True if "true" == ServiceUtility.get_tag_content("return", element, name_space) else False
        except Exception as ex:
            print(ex)
            return False

    @staticmethod
    def _parse_instances_info(account: SiteAccount, zone: str, parameters: dict, dry_run=False):
        try:
            element = ServiceUtility.make_request(account, EndPoint.EC2, zone, "DescribeInstances",
                                                  dry_run, parameters, use_https=True)
            name_space, tag = ServiceUtility.get_tag_uri_and_name(element)
            InstanceRequestSet = [x for x in element.iter("{{{0:s}}}instancesSet".format(name_space,))]
            # InstanceRequestSet = element.find("{{{0:s}}}instancesSet".format(name_space,))
            info = []
            target_tag = "{{{0:s}}}item".format(name_space,)
            for item_set in InstanceRequestSet:
                for item in item_set.findall(target_tag):
                    print(item.tag)
                    state = item.find("{{{0:s}}}instanceState".format(name_space,))
                    item_status = state[1].text
                    item_code = state[0].text
                    item_type = ServiceUtility.get_tag_content("instanceType", item, name_space)
                    item_instance_id = ServiceUtility.get_tag_content("instanceId", item, name_space)
                    create_time = ServiceUtility.get_tag_content("launchTime", item, name_space)
                    public_ip = ServiceUtility.get_tag_content("ipAddress", item, name_space)
                    private_ip = ServiceUtility.get_tag_content("privateIpAddress", item, name_space)
                    temp = InstanceInfo()
                    temp.ins_type = item_type
                    temp.ins_id = item_instance_id
                    temp.state = item_status
                    temp.status_code = item_code
                    temp.launch_time = create_time
                    temp.private_ip = private_ip
                    temp.public_ip = public_ip
                    info.append(temp)
            return info
        except Exception as ex:
            print(ex)
            return None

    @staticmethod
    def get_instances_by_tag(account: SiteAccount, zone: str, tag_key: str,  tag_value, dry_run=False):
        parameters = {
            "Filter.1.Name": "tag:{0:s}".format(tag_key,),
            "Filter.1.Value.1": str(tag_value),
            # "Filter.1.Name": "tag-value",
            # "Filter.1.Value.1": str(tag_value),
        }
        return EC2Resource._parse_instances_info(account, zone, parameters, dry_run)


    @staticmethod
    def start_normal_instances(account: SiteAccount, image_id: str, key_name: str, security_group: str,
                               instance_type: str, zone: str, instance_count: int, dry_run=False):
        parameters = {
            "MaxCount": instance_count,
            "MinCount": instance_count,
            "ImageId": image_id,
            "KeyName": key_name,
            "SecurityGroupId.1": security_group,
            "InstanceType": instance_type,
            # "LaunchSpecification.SubnetId": subnet,
            "Placement.AvailabilityZone": zone,
        }
        try:
            element = ServiceUtility.make_request(account, EndPoint.EC2, zone, "RunInstances",
                                                  dry_run, parameters, use_https=True)
            print(element)
        except Exception as ex:
            print(ex)


    @staticmethod
    def terminate_instances(account: SiteAccount, zone: str, instance_ids: [],
                            target_states=[InstanceState.ShutDown, InstanceState.Terminated],
                            dry_run=False) ->([], bool):
        parameters = {
        }
        counter = 1
        for item in instance_ids:
            if isinstance(item, str):
                parameters.update({"InstanceId.{0:d}".format(counter,): item})
                counter += 1
        try:
            all_state_valid = True
            element = ServiceUtility.make_request(account, EndPoint.EC2, zone, "TerminateInstances",
                                                  dry_run, parameters, use_https=True)
            name_space, tag = ServiceUtility.get_tag_uri_and_name(element)
            InstanceRequestSet = element[1]
            info = []
            target_tag = "{{{0:s}}}item".format(name_space,)
            for item in InstanceRequestSet.findall(target_tag):
                instanceId = ServiceUtility.get_tag_content("instanceId", element, name_space)
                currentState = item.find("{{{0:s}}}currentState".format(name_space,))
                status = ServiceUtility.get_tag_content("name", currentState, name_space)
                temp = TerminateInstanceResponse()
                temp.state = status
                temp.ins_id = instanceId
                if status not in target_states:
                    all_state_valid = False
                info.append(temp)
            return info, all_state_valid
        except Exception as ex:
            print(ex)
            return [], False