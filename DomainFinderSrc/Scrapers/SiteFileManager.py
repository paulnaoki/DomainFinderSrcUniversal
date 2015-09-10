from DomainFinderSrc.Utilities import FileIO
from DomainFinderSrc.Utilities import FilePath
import threading
import os
from DomainFinderSrc.Scrapers.LinkChecker import LinkChecker


class SiteFileManager(object):
    def __init__(self, base_dir_path: str, file_name: str):
        self._dir_path = base_dir_path + "/" + file_name + "/"
        self._file_name = file_name
        self.default_css_folder_path = self._dir_path + "/css/"
        self.default_image_folder_path = self._dir_path + "/images/"
        self.default_js_folder_path = self._dir_path + "/js/"
        self._stop_event = threading.Event()
        self._task_count = 0
        self._task_lock = threading.RLock()

    def _acquire_task(self):
        with self._task_lock:
            self._task_count += 1

    def _release_task(self):
        with self._task_lock:
            self._task_count -= 1

    def is_finished(self):
        with self._task_lock:
            task_count = self._task_count
        return True if task_count == 0 and self._stop_event.is_set() else False

    def exist_in_path(self, sub_path):
        full_path = self._dir_path + sub_path
        full_path = full_path.replace("//", "/")
        return os.path.exists(full_path)

    def read_from_file(self, sub_path, mode="t"):
        full_path = self._dir_path + sub_path
        full_path = full_path.replace("//", "/")
        if self.exist_in_path(sub_path):
            return FileIO.FileHandler.read_all_from_file(full_path, mode)
        else:
            return ''

    def write_to_file(self, sub_path: str, data, mode="t"):
        if not self._stop_event.is_set() and data is not None:
            #self._acquire_task()
            full_path = self._dir_path + sub_path
            full_path = full_path.replace("//", "/")
            print("write to file:", full_path)
            FileIO.FileHandler.create_file_if_not_exist(full_path)
            if mode == "t":  # used to write text file
                with open(full_path, mode="wt", encoding="utf-8") as file:
                    file.write(data)
                    file.close()
            elif mode == "b":  # used to write image file
                with open(full_path, mode="wb") as file:
                    file.write(data)
                    file.close()
            #self._release_task()

    def download_file(self, sub_path: str, url: str, timeout=5, retries=1, redirect=3):
        full_path = self._dir_path + sub_path
        full_path = full_path.replace("//", "/")
        s = LinkChecker.get_common_request_session(retries=retries, redirect=redirect)
        # NOTE the stream=True parameter
        r = s.get(url, stream=True, timeout=timeout)
        FileIO.FileHandler.create_file_if_not_exist(full_path)
        with open(full_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
                    f.flush()
            f.close()

    def set_stop(self):
        self._stop_event.set()