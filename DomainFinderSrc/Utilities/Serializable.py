import collections
from functools import reduce
import sys
import json
from copy import deepcopy, copy


class Serializable:

    # def __init__(self):
    #     pass
    #
    # __call__ = __init__

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

    def get_non_none_parameters(self):
        new_dict = {}
        for k, v in self.__dict__.items():
            if v is not None:
                new_dict.update({k: v})
        return new_dict

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

    def get_serializable_json(self, invert_back=True) -> str:
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


# def _get_dict(obj) -> dict:
#     temp = {}
#     for item in obj.__slots__:
#         temp.update({item: getattr(obj, item)})
#     return temp

class NamedMutableSequence(collections.Sequence, Serializable):
    """
    # class Point(NamedMutableSequence):
    # __slots__ = ('x', 'y')
    # >>> p = Point(0, 0)
    # >>> p.x = 10
    # >>> p
    # Point(x=10, y=0)
    # >>> p.x *= 10
    # >>> p
    # Point(x=100, y=0)
    """
    __slots__ = ()
    # __dict__ = {}

    def __init__(self, *a, **kw):
        # self.__dict__ = {}
        slots = self.__slots__
        for k in slots:
            v = kw.get(k)
            setattr(self, k, v)
            self.__dict__.update({k: v})

        if a:
            for k, v in zip(slots, a):
                setattr(self, k, v)
                self.__dict__.update({k: v})

    def __str__(self):
        clsname = self.__class__.__name__
        values = ', '.join('%s=%r' % (k, getattr(self, k))
                           for k in self.__slots__)
        return '%s(%s)' % (clsname, values)

    __repr__ = __str__

    def __getitem__(self, item):
        # return self.__dict__.get(item)
        return getattr(self, self.__slots__[item])

    def __setitem__(self, item, value):
        # self.__dict__.update({item: value})
        setattr(self, self.__slots__[item], value)

    def __getattr__(self, item):
        return self.__dict__.get(item)

    def __setattr__(self, key, value):
        self.__dict__.update({key: value})
        # setattr(self, self.__slots__[key], value)

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        # result = NamedMutableSequence()
        # result.__class__ = self.__class__
        # result.__slots__ = self.__slots__
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            if v is not None:
                # setattr(result, k, copy(v))
                setattr(result, k, deepcopy(v, memo))
            else:
                setattr(result, k, None)
        return result

    def __len__(self):
        return len(self.__slots__)


# not mutable tuple with default values, not so useful
def namedtuple_with_defaults(typename, field_names, default_values=[]):
    """
    # >>> Node = namedtuple_with_defaults('Node', 'val left right')
    # >>> Node()
    # Node(val=None, left=None, right=None)
    # >>> Node = namedtuple_with_defaults('Node', 'val left right', [1, 2, 3])
    # >>> Node()
    # Node(val=1, left=2, right=3)
    # >>> Node = namedtuple_with_defaults('Node', 'val left right', {'right':7})
    # >>> Node()
    # Node(val=None, left=None, right=7)
    # >>> Node(4)
    # Node(val=4, left=None, right=7)
    :param typename:
    :param field_names:
    :param default_values:
    :return:
    """
    T = collections.namedtuple(typename, field_names)
    T.__new__.__defaults__ = (None,) * len(T._fields)
    if isinstance(default_values, collections.Mapping):
        prototype = T(**default_values)
    else:
        prototype = T(*default_values)
    T.__new__.__defaults__ = tuple(prototype)
    return T
