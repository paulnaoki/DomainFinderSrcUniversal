import threading
import time


class threadFlag:
    def __init__(self, defaultV=False):
        self._flag = defaultV
        self._flag_lock = threading.RLock()

    def set_flag(self, value=True):
        while not self._flag_lock.acquire(False):
            time.sleep(0.1)
        self._flag = value
        self._flag_lock.release()

    def is_flag_set(self):
        while not self._flag_lock.acquire(False):
            time.sleep(0.1)
        flag_v = self._flag
        self._flag_lock.release()
        return flag_v