from DomainFinderSrc.Utilities import FilePath
from DomainFinderSrc.Utilities.FileIO import FileHandler
from DomainFinderSrc.Utilities.Logging import CsvLogger, ErrorLogger
import os
import csv


class ProxyStruct:
    def __init__(self, addr: str, port: int, alt_port=0, user_name="", psd=""):
        self.addr = addr
        self.port = port
        self.alt_port = alt_port
        self.user_name = user_name
        self.psd = psd

    def __str__(self):
        if len(self.user_name) > 0:
            return ":".join([self.addr, str(self.port), self.user_name, self.psd])
        else:
            return ":".join([self.addr, str(self.port)])

    def str_no_auth(self):
        return ":".join([self.addr, str(self.port)])

class ProxyManager:
    def __init__(self):
        self._file_path = FilePath.get_proxy_file_path()

    def add_proxies(self, proxies: []):
        if proxies is not None:
            convtered = []
            for proxy in proxies:
                if isinstance(proxy, ProxyStruct):
                    convtered.append((proxy.addr, proxy.port, proxy.alt_port, proxy.user_name, proxy.psd))
            FileHandler.create_file_if_not_exist(self._file_path)
            CsvLogger.log_to_file_path(self._file_path, convtered)

    def delete_proxy_file(self):
        FileHandler.remove_file_if_exist(self._file_path)

    def get_proxies(self) -> []:
        """
        get a list of proxies
        :return:proxies in ProxyStruct format
        """
        if os.path.exists(self._file_path):
            data = []
            with open(self._file_path, mode='r') as csv_f:
                reader = csv.reader(csv_f)
                for addr, port, alt_port, user_name, psd in reader:
                    int_port = int(port)
                    if len(alt_port) == 0:
                        int_alt_port = 0
                    else:
                        int_alt_port = int(alt_port)
                    data.append(ProxyStruct(addr, int_port, int_alt_port, user_name, psd))
                csv_f.close()
            return data
        else:
            return []

