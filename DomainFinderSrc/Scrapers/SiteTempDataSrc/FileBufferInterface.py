import time
from collections import deque
from threading import RLock
from DomainFinderSrc.Utilities.Logging import *
from DomainFinderSrc.Utilities.Serializable import Serializable
import os
import sqlite3
from DomainFinderSrc.Utilities.FileIO import FileHandler
from DomainFinderSrc.Utilities.FilePath import get_recovery_dir_path


class FileBuffDefaultState(Serializable):
    def __init__(self, progress: int=0, all_data: int=0):
        self.progress = progress
        self.all_data = all_data


class FileBuffInterface:
    def __init__(self, file_name, output_buff_size=200, output_f=1000, power_save_mode=False, terminate_callback=None):
        """
        Generic Interface for buffering large amount of data using file, instead of memory
        :param file_path: path to file
        :param output_buff_size: size of output buffer
        :param output_f:  output frequency
        :param power_save_mode: if enabled, do not forget to implement recovery_from_power_cut() and
        get_state_for_power_save_mode() if you have non standard states. it will the state to recover from programme or
        power failure during a long running process.also you can set self._power_save_period to meet your need.
        :return:
        """
        self._file_name = file_name
        self._recovery_file_path = get_recovery_dir_path(self._file_name) + ".power.db"
        self._output_buff_size = output_buff_size
        self._output_queue = deque()
        self._input_buff = []
        self._input_convert_tuple = True
        self._output_counter = 0
        self._continue_lock = RLock()
        self._append_lock = RLock()
        self._continue = True
        self._total_record = 0
        self._update_record_period = 30
        self._power_save_period = 30
        self._min_outptu_period = 1/output_f
        self._terminate_callback = terminate_callback

        self._input_t = threading.Thread(target=self.input_cycling, name="input_buf_t")
        self._output_t = threading.Thread(target=self.output_cycling, name="output_buf_t")
        self._power_save_t = threading.Thread(target=self.power_save_cycle, name="power_t")

        self._power_save_mode = power_save_mode
        if power_save_mode:
            self._read_from_power_save_db()

    def set_db_update_interval(self, interval: int):
        if interval > 0:
            self._update_record_period = interval

    def _write_to_power_save_db(self) -> bool:
        data = self.get_state_for_power_save_mode()
        if isinstance(data, Serializable):
            FileHandler.create_file_if_not_exist(self._recovery_file_path)
            try:
                db = sqlite3.connect(self._recovery_file_path)
                cur = db.cursor()
                cur.execute("CREATE TABLE IF NOT EXISTS STATE_TAB(STATE TEXT UNIQUE, STATE_V TEXT);")
                data_converted = data.get_serializable_json()
                cur.execute("INSERT OR REPLACE INTO STATE_TAB (STATE, STATE_V) VALUES ( ?, ?);", ("state", data_converted))
                db.commit()
                db.close()
                return True
            except Exception as ex:
                ErrorLogger.log_error("FileBuffInterface", ex, "_write_to_power_save_db() " + self._recovery_file_path)
                return False
        else:
            return False

    def _read_from_power_save_db(self):
        if os.path.exists(self._recovery_file_path):
            data_converted = None
            try:
                db = sqlite3.connect(self._recovery_file_path)
                cur = db.cursor()
                cur_ex = cur.execute("SELECT STATE_V FROM STATE_TAB WHERE STATE={0:s};".format("state",))
                data = cur_ex.fetchone()[0]
                db.close()
                data_converted = Serializable.get_deserialized_json(data)
            except Exception as ex:
                ErrorLogger.log_error("FileBuffInterface", ex, "_read_from_power_save_db() " + self._recovery_file_path)
            self.recovery_from_power_cut(data_converted)

    def remove_power_save_db(self):
        FileHandler.remove_file_if_exist(self._recovery_file_path)

    def recovery_from_power_cut(self, data: Serializable):
        """
        if you have costumized state, pls implement your own Serializable and override this method
        :param data:
        :return:
        """
        if data is None:
            return
        if isinstance(data, FileBuffDefaultState):
            self._total_record = data.all_data
            self._output_counter = data.progress
        else:
            pass

    def get_state_for_power_save_mode(self) ->Serializable:
        """
        if you have costumized state, pls implement your own Serializable and override this method
        :return:
        """
        return FileBuffDefaultState(self._output_counter, self._total_record)

    def set_progress(self, count: int):
        self._output_counter = count

    def start_input_output_cycle(self):
        self._input_t.start()
        self._output_t.start()
        if self._power_save_mode:
            self._power_save_t.start()

    def get_total_record(self):
        return self._total_record

    def reset(self):
        self._input_buff.clear()
        self._output_counter = 0
        self._total_record = 0
        self._continue = False
        if self._input_t.is_alive():
            self._input_t.join()
        if self._output_t.is_alive():
            self._output_t.join()
        if self._power_save_mode and self._power_save_t.is_alive():
            self._power_save_t.join()
        self._continue = True
        self._input_t = threading.Thread(target=self.input_cycling, name="input_buf_t")
        self._output_t = threading.Thread(target=self.output_cycling, name="output_buf_t")
        if self._power_save_mode:
            self._power_save_t = threading.Thread(target=self.power_save_cycle, name="power_t")

    def set_continue_lock(self, can_contiune=True):
        with self._continue_lock:
            self._continue = can_contiune

    def can_continue(self):
        with self._continue_lock:
            can_continue = self._continue
        return can_continue

    def __next__(self):
        next_item = None
        while self.can_continue():
            if len(self._output_queue) > 0:
                next_item = self._output_queue.popleft()
                if next_item is not None:
                    break
            time.sleep(self._min_outptu_period)
        if next_item is not None:
            return next_item
        else:
            if self._terminate_callback is not None:
                self._terminate_callback()
            raise StopIteration

    def append_to_buffer(self, new_data_list, convert_tuple=True):
       # with self._append_lock:
        self._input_convert_tuple = convert_tuple
        self._input_buff += new_data_list

    def format_output(self, data):
        """
        convert object in output buffer to actual use
        :param data:
        :return:
        """
        return data

    def format_input(self, data):
        return data

    def __iter__(self):
        return self

    def get_task_done_count(self):
        raise NotImplementedError

    def read(self, file=None) -> []:
        """
        read data from file
        :return:
        """
        raise NotImplementedError

    def write(self, data: [], file=None) -> bool:
        raise NotImplementedError

    def update_total_in_file(self):
        pass

    def use_same_connection_to_file(self):
        """
        it means it uses same thread to read file, other thread to write file, the file is kepted alive in both cases.
        subclass must impliment open_file_oject() and close_file_object() if return is True
        :return:
        """
        return False

    def open_file_object(self):
        raise NotImplementedError

    def close_file_object(self, file):
        raise NotImplementedError

    def input_cycling(self):
        file = None
        if self.use_same_connection_to_file():
            file = self.open_file_object()
        while True:
            if not self.can_continue() or not self._continue:
                break
            #self._append_lock.acquire()
            input_length = len(self._input_buff)
            if input_length > 500000:
                input_length = 500000
            if input_length > 0:
                #print("want to add more sites ", input_length)
                input_array = self._input_buff[:input_length]
                #self._append_lock.release()
                if self.write(data=input_array, file=file):  # long time process
                    #PrintLogger.print("input result count: " + str(input_length))
                    #self._append_lock.acquire()
                    try:
                        #self._append_lock.acquire()
                        self._input_buff = self._input_buff[input_length:]
                    except:
                        pass
                    finally:
                        pass
                       # self._append_lock.release()
            else:
                #self._append_lock.release()
                pass
            time.sleep(1)
        if file is not None:
            self.close_file_object(file)

    def output_cycling(self):
        self._total_record = self.update_total_in_file()
        ref_time = time.time()
        file = None
        if self.use_same_connection_to_file():
            file = self.open_file_object()
        while True:
            if not self.can_continue()or not self._continue:
                break
            #current_time = time.time()
            progress = self.get_task_done_count()
            # if current_time - ref_time > self._update_record_period:
            #     ref_time = current_time
            #     self._total_record = self.update_total_in_file()
            #     print("FileBufferInterface in datasource total record is:", self._total_record, "progress is:", progress)
            #remaining = len(self.output_queue)
            gap = self._output_counter - progress

            if gap < self._output_buff_size/2 and self._total_record > self._output_counter:
                stored_item = self.read(file=file)
                if len(stored_item) > 0:
                    for item in stored_item:
                        self._output_queue.append(self.format_output(item))
                    self._output_counter += len(stored_item)
                elif self.use_same_connection_to_file():  # the data selected in previous connection has been depleted, so re-open the file so that it can read again
                    self.close_file_object(file)
                    file = self.open_file_object()
            else:
                current_time = time.time()
                if current_time - ref_time > self._update_record_period:
                    ref_time = current_time
                    self._total_record = self.update_total_in_file()
                    print("FileBufferInterface in datasource", self._file_name, " total record is:", self._total_record, "progress is:", progress)
            time.sleep(1)
        if file is not None:
            self.close_file_object(file)

    def power_save_cycle(self):
        last_save = time.time()
        while True:
            if not self.can_continue() or not self._continue:
                break
            current_time = time.time()
            if current_time - last_save >= self._power_save_period:
                if self._write_to_power_save_db():
                    last_save = current_time
            time.sleep(1)

    def terminate(self):
        self._continue = False
        print("set to terminate in file buffer:", self._file_name, "index:", self._output_counter, "total:", self._total_record)
        #print("continue lock is disabled")
        if self._input_t.is_alive():
            self._input_t.join()
        #print("input cycle stopped")
        if self._output_t.is_alive():
            self._output_t.join()
        #print("output cycle stopped")
        if self._power_save_mode:
            self._power_save_t.join()
        #print("power save cycle stopped")