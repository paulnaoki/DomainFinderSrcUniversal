import os
import sqlite3
from DomainFinderSrc.Utilities.FileIO import FileHandler
from DomainFinderSrc.Utilities.FilePath import get_db_buffer_default_dir
from DomainFinderSrc.Utilities.Logging import PrintLogger, ErrorLogger
import time

class TempDBInterface:
    sqlite_temp_suffix = "-journal"
    sqlite_wal_suffix = "-wal"

    def __init__(self, ref: str, creation_strategy: str, save_dir="", file_limit=1000000,
                 table_name="TEMP", write_ahead_mode=True):
        if len(save_dir) == 0:
            default_dir = get_db_buffer_default_dir()
        else:
            default_dir = save_dir
        self._table_name = table_name
        self._write_ahead_mode = write_ahead_mode
        FileHandler.create_file_if_not_exist(default_dir)
        self.filename = default_dir + ref
        # file_exist = os.path.exists(self.filename)
        self.db = sqlite3.connect(self.filename, timeout=10)
        self.cur = self.db.cursor()
        #self.cur.execute("PRAGMA journal_mode = MEMORY")
        #if not file_exist:
        if self._write_ahead_mode:
            self.cur.execute("PRAGMA journal_mode = WAL;")
            self.cur.execute("PRAGMA synchronous = OFF;")
        self.exclusive_access_file_limit = file_limit
        # cannot ensure uniqueness of data in multithread access
        #self.cur.execute("CREATE TABLE IF NOT EXISTS TEMP (LINK TEXT, RS_CODE INTEGER, LEV INTEGER, L_TYPE INTEGER, PRIMARY KEY(LINK));")
        self.cur.execute(creation_strategy)
        self.db.commit()
        #print("open connection: ", self.connection_id)
        #con = sqlite3.Cursor()

    def _is_write_ahead_file_large(self):
        wal_file = self.filename + TempDBInterface.sqlite_wal_suffix
        journal_file = self.filename + TempDBInterface.sqlite_temp_suffix
        if os.path.exists(wal_file):
            # print("checking file:", wal_file)
            file_size = os.path.getsize(wal_file)
            is_large = True if file_size > self.exclusive_access_file_limit else False
            # if is_large:
            #     print("file is too large.")
            # else:
            #     print("file is ok for now.")
            return is_large
        # elif os.path.exists(journal_file):
        #     print("checking file:", journal_file)
        #     file_size = os.path.getsize(journal_file)
        #     is_large = True if file_size > self.exclusive_access_file_limit else False
        #     if is_large:
        #         print("file is too large.")
        #     else:
        #         print("file is ok for now.")
        #     return is_large
        else:
            # print("file doesnt is not in dir.")
            return False

    def should_vaccum_and_exclusive_access(self):
        if self._write_ahead_mode:
            return self._is_write_ahead_file_large()
        else:
            return False

    def enter_exclusive_mode(self):
        self.cur.execute("PRAGMA locking_mode = EXCLUSIVE;")

    def vaccum_db(self):
        try:
            self.db.interrupt()
        except Exception as ex:
            PrintLogger.print(ex)
        finally:
            self.db = sqlite3.connect(self.filename, timeout=10)
            self.db.execute("VACUUM {0:s};".format(self._table_name,))
            # self.db.execute("VACUUM;")

    def is_vaccum_finished(self):
        return self._is_write_ahead_file_large()

    def get_db(self):
        return self.db

    def get_cur(self):
        return self.cur

    def close(self):
        try:
            #print("close connection: ", self.connection_id)
            self.db.close()
        except Exception as ex:
            msg = "error in SiteTempDatabase.close(): trying to close db but failed, " + self.filename
            ErrorLogger.log_error("SiteTempDatabase", ex, msg)

    @staticmethod
    def force_clear(ref: str, dir_path="")->True:
        """
        force to remove database in file
        :param ref: the file name
        :return: True if remove successfully, else false
        """
        if len(dir_path) == 0:
            dir_path = get_db_buffer_default_dir()
        remove_ok = False
        filename = dir_path + ref
        try:
            time.sleep(1)
            # print("going to remove: ", filename)
            if os.path.exists(filename):
                os.remove(filename)
                # print("file removed: ", filename)
            temp_file = filename + TempDBInterface.sqlite_temp_suffix
            # print("going to remove:", temp_file)
            if os.path.exists(temp_file):
                os.remove(temp_file)
                # print("file removed: ", temp_file)
            # print("going to remove:", filename + TempDBInterface.sqlite_wal_suffix)
            if os.path.exists(filename + TempDBInterface.sqlite_wal_suffix):
                os.remove(filename + TempDBInterface.sqlite_wal_suffix)
                # print("file removed: ", filename + TempDBInterface.sqlite_wal_suffix)
            remove_ok = True
        except Exception as ex:
            msg = "error in SiteTempDatabase.force_clear(), " + filename
            ErrorLogger.log_error("SiteTempDatabase", ex, msg)
        finally:
            return remove_ok


class SiteTempDatabase(TempDBInterface):
    def __init__(self, ref: str, save_dir=""):
        creation = "CREATE TABLE IF NOT EXISTS TEMP (LINK TEXT UNIQUE, RS_CODE INTEGER, " \
                   "LEV INTEGER, L_TYPE INTEGER, ID INTEGER PRIMARY KEY AUTOINCREMENT);"
        TempDBInterface.__init__(self, ref, creation_strategy=creation, save_dir=save_dir)


class SiteTempExternalDatabase(TempDBInterface):
    def __init__(self, ref: str, save_dir=""):
        creation = "CREATE TABLE IF NOT EXISTS TEMP (LINK TEXT UNIQUE, RS_CODE INTEGER, ID INTEGER PRIMARY KEY AUTOINCREMENT);"
        TempDBInterface.__init__(self, ref, creation_strategy=creation, save_dir=save_dir)