from DomainFinderSrc.Utilities.Serializable import Serializable, NamedMutableSequence

# InstanceInfo = namedtuple_with_defaults("InstanceInfo", "ins_id ins_type public_ip private_ip launch_time")
# SpotRequestInfo = namedtuple_with_defaults("SpotRequestInfo", "req_id state status instance_ids")


class InstanceInfo(NamedMutableSequence):
    __slots__ = ('ins_id', 'request_id', 'ins_type', 'public_ip', 'private_ip', 'launch_time', 'state', 'status_code')


class SpotRequestInfo(NamedMutableSequence):
    __slots__ = ('req_id', 'state', 'status', 'ids')


class CancelledSpotInstanceResponse(NamedMutableSequence):
    __slots__ = ('req_id', 'state')


class TerminateInstanceResponse(NamedMutableSequence):
    __slots__ = ('ins_id', 'state')
# class InstanceInfo(Serializable):
#     def __init__(self, ins_id: str="", ins_type: str="", public_ip: str="", private_ip: str="", launch_time: str=""):
#         self.ins_id = ins_id
#         self.ins_type = ins_type
#         self.public_ip = public_ip
#         self.private_ip = private_ip
#         self.launch_time = launch_time
#
#     def __str__(self):
#         return str(self.__dict__)
