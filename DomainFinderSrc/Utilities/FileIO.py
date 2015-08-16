import os
from os import path
import shutil
import time


class FileHandler:
    CheckFrequency = 0.5  # check every 0.5 second

    def __init__(self, timeout=10):
        """
        :param timeout: timeout when checking time is greater then it
        :return:
        """
        # self.driver = driver
        self.timeout = timeout

    @staticmethod
    def create_file_if_not_exist(file_path: str):
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))

    @staticmethod
    def remove_file_if_exist(file_path: str):
        if os.path.exists(file_path):
            os.remove(file_path)

    @staticmethod
    def append_line_to_file(file_path: str, data):
        """
        :param file_path: path to file, if not exist it will create a new file
        :param data: a list of string
        :return: True if write s
        """
        try:
            with open(file_path, "a") as f:
                f.write(data + "\n")
                f.close()
            return True
        except Exception as ex:
            print(ex)
            return False

    @staticmethod
    def read_lines_from_file(file_path: str, option="t", remove_blank_line=True) -> []:
        if not os.path.exists(file_path):
            return []
        if option not in ['b', 't']:
            raise ValueError("option is not valid.")
        try:
            with open(file_path, mode="r"+option) as f:
                raw = f.readlines()
                if not remove_blank_line:
                    data = raw
                else:
                    data = [x.replace('\n', '') for x in raw]
                f.close()
            return data
        except Exception as ex:
            raise ex

    @staticmethod
    def append_lines_to_file(file_path: str, data: [], option="a"):
        """
        :param file_path: path to file, if not exist it will create a new file
        :param data: a list of string
        :param option: 'x' for rewrite, 'w' for truncate write, 'a' for append, 'b' for binary mode, 't' for text mode.
        for instance: 'wt'
        :return: True if write without error
        """
        for i in option:
            if i not in ['w', 'x', 'a', 'b', 't']:
                raise ValueError("option is not valid.")
        FileHandler.create_file_if_not_exist(file_path)
        try:
            with open(file_path, option) as f:
                for line in data:
                    f.write(line + "\n")
                f.close()
            return True
        except Exception as ex:
            raise ex

    def check_download_completed(self, fileLocation: str):
        """
        Check by polling the file location at frequency of FileHandler.CheckFrequency
        :param fileLocation: where the file should be located, beware of different OS file path
        :return:True if the file is found, else False
        """
        counter = 0
        while counter < self.timeout - FileHandler.CheckFrequency:
            if os.path.exists(fileLocation):
                return True
            else:
                counter += FileHandler.CheckFrequency
                time.sleep(FileHandler.CheckFrequency)

        return False

    def check_download_dir_not_empty(self, dirLocation: str):
        """
        :param dirLocation:  dir to file location
        :return: True if it has found some files, else False after timeout set by self.timeout
        """
        counter = 0
        while counter < self.timeout - FileHandler.CheckFrequency:
            if path.exists(dirLocation) and len(os.listdir(dirLocation)) > 0:
                return True
            else:
                counter += FileHandler.CheckFrequency
                time.sleep(FileHandler.CheckFrequency)

    def get_files_from_dir(self, dirLocation: str, extension: str="") -> []:
        if dirLocation is not None and path.exists(dirLocation):
            files = os.listdir(dirLocation)
            if len(files) > 0:
                if extension is not None and extension != "":
                    return [path.join(dirLocation, x) for x in files if x.endswith(extension)]
                else:
                    return [path.join(dirLocation, x) for x in files if path.isfile(path.join(dirLocation, x))]
            else:
                return None

    @staticmethod
    def clear_dir(dirLocation: str):
        if path.exists(dirLocation):
            for root, dirs, files in os.walk(dirLocation):
                for f in files:
                    os.unlink(os.path.join(root, f))
                for d in dirs:
                    shutil.rmtree(os.path.join(root, d))

    @staticmethod
    def clear_file(fileLocation: str):
        if path.exists(fileLocation):
            os.unlink(fileLocation)