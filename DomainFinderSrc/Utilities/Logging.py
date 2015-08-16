import time
import threading
from multiprocessing import Event
import csv
import datetime
import pytz
from DomainFinderSrc.Utilities.FileIO import FileHandler
from DomainFinderSrc.Utilities.FilePath import get_log_dir
import DomainFinderSrc
from DomainFinderSrc.Utilities.Dispatcher import TimeoutDispatcher


class PrintLogger:

    @staticmethod
    def print(data):
        if data is not None and DomainFinderSrc.IS_DEBUG:
            print(str(data))


class ErrorLogger:
    FILE_NAME = "Error.csv"
    Counter = 0

    @staticmethod
    def log_error(ref: str, error: Exception, addtional: str=""):
        path = get_log_dir() + ErrorLogger.FILE_NAME
        try:
            FileHandler.create_file_if_not_exist(path)
            lines = []
            lines.append(ref)
            lines.append("{0:d} {1:s}".format(ErrorLogger.Counter, str(datetime.datetime.now(tz=pytz.utc))))
            lines.append(str(error))
            if len(addtional) > 0:
                lines.append(addtional)
            with open(path, mode='a', newline='') as csv_file:
                wr = csv.writer(csv_file, delimiter=',')
                wr.writerow(lines)
                csv_file.close()
            # lines.append("")
            # FileHandler.append_lines_to_file(path, lines)
            ErrorLogger.Counter += 1
        except:
            pass


class CsvLogger:
    @staticmethod
    def log_to_file_path(file_path: str, rows: [()]):
        if len(rows) > 0:
            try:
                path = file_path
                if not path.endswith(".csv"):
                    path += ".csv"
                FileHandler.create_file_if_not_exist(path)
                with open(path, mode='a', newline='') as csv_file:
                    wr = csv.writer(csv_file, delimiter=',')
                    for row in rows:
                        wr.writerow(row)
                    csv_file.close()
            except Exception as ex:
                ErrorLogger.log_error("CsvLogger", ex, "log_to_file_path()")

    @staticmethod
    def log_to_file(file_name: str, rows: [()], dir_path=""):
        """
        write data to a log file in .csv format
        :param file_name:
        :param rows:
        :return:
        """
        if len(rows) > 0:
            if len(dir_path) == 0:
                path = get_log_dir() + file_name
            else:
                if not dir_path.endswith("/"):
                    path = dir_path + "/" + file_name
                else:
                    path = dir_path + file_name
            CsvLogger.log_to_file_path(path, rows)


class ProgressLogInterface:
    def get_file_name(self) -> str:
        """
        the file name used to save in file system.
        :return:
        """
        raise NotImplementedError

    def get_column_names(self) -> []:
        """
        the column name for each prograss entry in get_prograss(), all in str format
        :return: array contains column names, length should match the length of prograss entries
        """
        raise NotImplementedError

    def get_progress(self) -> []:
        """
        get the prograss data in tuple format, so that it can be used to complie to standard format
        :return: array contains prograss data, which has the exact length of column names in get_column_names()
        """
        raise NotImplementedError

    def get_limit(self) -> int:
        """
        the number of samples you want to collect.
        :return: max number of samples
        """
        raise NotImplementedError


class ProgressLogger(threading.Thread):

    def __init__(self, interval: int, ref: ProgressLogInterface, stop_event: Event):
        """
        logging prograss for long running method
        :param interval: period of logging in second
        :param ref: the reference object invoked logging
        :param stop_event: event to stop logging
        :return:
        """
        threading.Thread.__init__(self)
        self._interval = interval
        self._ref = ref
        self._stop_event = stop_event
        self.begin_time = int(time.time())
        self._ref_time = self.begin_time
        self._path = get_log_dir() + "Progress/"
        temp = ref.get_file_name()
        if len(temp) > 200:
            filename = temp[0:199]
        else:
            filename = temp
        if not filename.endswith(".csv"):
            filename += ".csv"
        self._file_path = self._path + filename
        FileHandler.create_file_if_not_exist(self._file_path)
        self._limit = ref.get_limit()
        self.limit_counter = 0

    def set_reference(self, sample_index: int, time_start: int):
        self.begin_time = time_start
        self._ref_time = self.begin_time
        self.limit_counter = sample_index

    def _append(self, data_row: []):
        try:
            PrintLogger.print(data_row)
            with open(self._file_path, mode='a', newline='') as csv_file:
                wr = csv.writer(csv_file, delimiter=',')
                                #quotechar='', quoting=csv.QUOTE_MINIMAL)
                wr.writerow(data_row)
                csv_file.close()
        except Exception as ex:
            ErrorLogger.log_error("ProgressLogger._append", ex)

    def report_progress(self):
        """
        call this method to write progress data to the log file
        :return:
        """
        self._ref_time = time.time()
        dispatcher = TimeoutDispatcher(self._ref.get_progress, timeout=10)
        progress = dispatcher.dispatch()
        if progress is not None:
            data = [self.limit_counter, int((self._ref_time - self.begin_time)/60)] + progress
            self._append(data)
            self.limit_counter += 1

    def run(self):
        FileHandler.create_file_if_not_exist(self._file_path)
        cols = ["Index", "Time/Min"] + self._ref.get_column_names()
        self._append(cols)
        while not self._stop_event.is_set() and self.limit_counter < self._limit:
            current_time = int(time.time())
            gap = current_time - self._ref_time
            if gap >= self._interval:
                self._ref_time = current_time
                self.report_progress()
            time.sleep(1)




