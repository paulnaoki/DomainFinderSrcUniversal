import psutil
import time
import sys
import enum
import os


class MachineType(enum.Enum):
    Linux = "Linux"
    Windows = "Windows"


class MachineInfo:

    @staticmethod
    def get_cpu(interval: int=1) ->(int, float):
        """
        :param interval: time interval to sample the cpu usage
        get the cpu info
        :return:(number of cpu, as percentage used)
        """
        if interval < 0:
            raise ValueError("CPU sampling interval cannot < 0")
        return psutil.cpu_count(), psutil.cpu_percent(interval)

    @staticmethod
    def get_memory_process(pid: int) ->float:
        default_v = 0
        try:
            pro = psutil.Process(pid=pid)
            default_v = pro.get_memory_info()[0] / float(2 ** 20)
        except:
            pass
        finally:
            return default_v

    @staticmethod
    def get_memory() -> (float, float):
        """
        get the memory info
        :return:(total memory in MB, memory used in percentage)
        """
        mem = psutil.virtual_memory()
        mem_total_in_MB = mem.total/(1024*1024)
        return mem_total_in_MB, mem.percent

    @staticmethod
    def get_network(interval: int=1) -> (float, float):
        """
        :param interval: time interval to sample the network usage
        get the network info
        :return:(MB recieved, MB send)
        """
        if interval < 0:
            raise ValueError("Network sampling interval cannot < 0")
        net_start = psutil.net_io_counters()
        time.sleep(interval)
        net_stop = psutil.net_io_counters()
        mb_received = (net_stop.bytes_recv - net_start.bytes_recv)/(1024*1024)
        mb_send = (net_stop.bytes_sent - net_start.bytes_sent)/(1024*1024)
        return mb_received, mb_send

    @staticmethod
    def get_machine_type():
        if sys.platform.startswith("win"):
            return MachineType.Windows
        else:
            return MachineType.Linux
