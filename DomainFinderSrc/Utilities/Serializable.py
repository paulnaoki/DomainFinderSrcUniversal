import collections
from functools import reduce
import sys
import json
from copy import deepcopy


class Serializable:

    def copy_attrs(self):
        return deepcopy(self)

    def copy_attrs_v1(self):
        cls = Serializable.get_class_full_name(self)
        module = Serializable.get_module(cls)
        instance = module()
        members = [attr for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("__")]
        for member in members:
            member_obj = getattr(self, member)
            setattr(instance, member, member_obj)
        return instance

    def get_serializable(self, invert_back=True):
        instance = self.copy_attrs()  # get a copy to avoid change the layout of the original obj
        if invert_back:
            cls = Serializable.get_class_full_name(instance)
            setattr(instance, "cls", cls)  # make it reversable when decoding
        members = [attr for attr in dir(instance) if not callable(getattr(instance, attr)) and not attr.startswith("__")]
        for member in members:
            member_obj = getattr(instance, member)
            if isinstance(member_obj, Serializable): # check to see if is subclass
                ser = member_obj.get_serializable(invert_back)
                delattr(instance, member)  # replace property
                setattr(instance, member, ser)
            elif isinstance(member_obj, collections.Iterable) and not isinstance(member_obj, str):
                for n, item in enumerate(member_obj):
                    if isinstance(item, Serializable):
                        member_obj[n] = item.get_serializable(invert_back)
        return instance.__dict__

    def get_serializable_json(self, invert_back=True):
        return json.dumps(self.get_serializable(invert_back))

    @staticmethod
    def get_class_full_name(object):
        cls_temp = object.__class__
        cls = cls_temp.__module__ + '.'+cls_temp.__name__
        return cls

    @staticmethod
    def get_module(module_name: str):
        module_list = module_name.split(".")
        if len(module_list) < 1:
            return None
        else:
            first_module = sys.modules.get(module_list[0])
            module_list = module_list[1:]
            return reduce(getattr, module_list, first_module)
        #return reduce(getattr, module_name.split("."), sys.modules[__name__])

    @staticmethod
    def get_deserialized(data: dict):
        cls_id = "cls"
        cls = data.get(cls_id)
        if cls is not None:
            #module = importlib.import_module("MiniServer.Common.SocketCommands")
            #instance = getattr(module, cls)
            module = Serializable.get_module(cls)
            instance = module()
            members = [x for x in data.keys() if not x == cls_id]
            #members = [attr for attr in dir(data) if not callable(getattr(data, attr)) and not attr.startswith("__") and not attr.startswith("cls")]
            for member in members:
                dict_obj = data.get(member)
                if isinstance(dict_obj, dict) and dict_obj.get(cls_id) is not None:
                    setattr(instance, member, Serializable.get_deserialized(dict_obj))
                elif isinstance(dict_obj, collections.Iterable) and not isinstance(dict_obj, str):
                    for n, item in enumerate(dict_obj):
                        if isinstance(item, dict):
                            inner_cls = item.get(cls_id)
                            if inner_cls is not None:
                                dict_obj[n] = Serializable.get_deserialized(item)
                    setattr(instance, member, dict_obj)
                else:
                    setattr(instance, member, dict_obj)
            return instance
        else:
            return None

    @staticmethod
    def get_deserialized_json(data: str):
        return Serializable.get_deserialized(json.loads(data))
