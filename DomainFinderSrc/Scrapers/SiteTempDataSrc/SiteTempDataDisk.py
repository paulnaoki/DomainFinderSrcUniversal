from sqlite3 import OperationalError
import time
from DomainFinderSrc.Scrapers.SiteTempDataSrc.DBStruct import SiteTempDatabase
from DomainFinderSrc.Scrapers.SiteTempDataSrc.SiteTempDataSrcInterface import *
from DomainFinderSrc.Utilities.Logging import ErrorLogger


class SiteTempDataDisk(SiteTempDataSrcInterface):
    def __init__(self, ref: str="temp", data=None, output_per_s=100,
                 ref_obj: SiteTempDataSrcRefInterface=None):
        super(SiteTempDataDisk, self).__init__(ref, data, ref_obj)
        self.output_f = 1/output_per_s  # limit this number otherwise will consume too much cpu
        #self.last_output_record = ""

    def count_all(self) -> int:
        try:
            temp = SiteTempDatabase(self.ref)
            temp.cur.execute(u"SELECT COUNT(*) FROM TEMP;")
            temp.db.commit()
            result = temp.cur.fetchone()
            temp.db.close()
            self.all_record = result[0]
        except:
            pass

        return self.all_record

    def count_onsite_links(self):
        temp = SiteTempDatabase(self.ref)
        on_site_type = OnSiteLink.TypeOnSite
        temp.cur.execute(u"SELECT COUNT(*) FROM TEMP WHERE L_TYPE=={0:d};".format(on_site_type,))
        temp.db.commit()
        result = temp.cur.fetchone()
        temp.db.close()
        return result[0]

    def get_all_outbound_links(self, response_code: int=ResponseCode.LinkBroken):
        tempdb = SiteTempDatabase(self.ref)
        total = self.count_all()
        for i in range(0, total):
            cur = tempdb.cur.execute("SELECT LINK, RS_CODE, LEV, L_TYPE FROM TEMP ORDER BY ID LIMIT 1 OFFSET {0:d};".format(i,))
            temp = cur.fetchone()
            link = temp[0]
            rs_code = temp[1]
            level = temp[2]
            link_type = temp[3]
            obj = OnSiteLink(link, response_code=rs_code, link_level=level, link_type=link_type)
            if link_type == OnSiteLink.TypeOutbound:
                if response_code == ResponseCode.All:
                    yield obj
                elif response_code == ResponseCode.LinkNotBroken and not ResponseCode.is_link_broken(rs_code):
                    yield obj
                elif response_code == ResponseCode.LinkBroken and ResponseCode.is_link_broken(rs_code):
                    yield obj
                elif rs_code == response_code:
                    yield obj
                else:
                    continue
            else:
                continue
        tempdb.close()

    def get_onsite_links(self, level: int, response_code: int):
        """
        :param level: the level where the link was in the domain
        :return: a list of OnSiteLink
        :exception: ValueError if level is < 0
        """
        if level < 0:
            raise ValueError()
        else:
            total = self.count_all()
            tempdb = SiteTempDatabase(self.ref)
            for i in range(0, total):
                cur = tempdb.cur.execute("SELECT LINK, RS_CODE, LEV, L_TYPE FROM TEMP ORDER BY ID LIMIT 1 OFFSET {0:d};".format(i,))
                temp = cur.fetchone()
                link = temp[0]
                rs_code = temp[1]
                level = temp[2]
                link_type = temp[3]
                obj = OnSiteLink(link, response_code=rs_code, link_level=level, link_type=link_type)
                if link_type == OnSiteLink.TypeOnSite:
                    if response_code == ResponseCode.All:
                        yield obj
                    elif response_code == ResponseCode.LinkNotBroken and not ResponseCode.is_link_broken(rs_code):
                        yield obj
                    elif response_code == ResponseCode.LinkBroken and ResponseCode.is_link_broken(rs_code):
                        yield obj
                    elif rs_code == response_code:
                        yield obj
                    else:
                        continue
                else:
                    continue
            tempdb.close()

    def is_link_in_page_list(self, link: str):
        #with self.get_lock:
        try:
            tempdb = SiteTempDatabase(self.ref)
            cur = tempdb.cur.execute("SELECT EXISTS(SELECT 1 FROM TEMP WHERE LINK=\'{0:s}\' LIMIT 1);".format(link,))
            #cur = tempdb.cur.execute("SELECT * FROM TEMP WHERE LINK=\'{0:s}\' LIMIT 1;".format(link,))
            result = cur.fetchone()
            tempdb.close()
            return True if result[0] == 1 else False
        except OperationalError:
            return True  # so that new data will not add to the db to cause further error

    def append_many(self, new_data_list, convert_tuple=True) -> bool:
        append_OK = False
        if new_data_list is not None and len(new_data_list) > 0:
            self.put_lock.acquire()
            try:
                tempdb = SiteTempDatabase(self.ref)
                try:
                    if convert_tuple:
                        to_tuple = [(x.link, x.response_code, x.link_level, x.link_type) for x in new_data_list]
                    else:
                        to_tuple = new_data_list
                    tempdb.cur.execute("BEGIN")
                    tempdb.cur.executemany("INSERT OR IGNORE INTO TEMP (LINK, RS_CODE, LEV, L_TYPE) "
                                           "VALUES (?, ?, ?, ?);", to_tuple)
                    tempdb.db.commit()
                    append_OK = True
                except OperationalError as ex:
                    msg = "error in SiteTempDataDisk.append_many(), operation failed. " + self.ref
                    ErrorLogger.log_error("SiteTempDataDisk", ex, msg)
            except Exception as outer_ex:
                msg = "error in SiteTempDataDisk.append_many() OperationalError, " + self.ref
                ErrorLogger.log_error("SiteTempDataDisk", outer_ex, msg)
            finally:
                self.put_lock.release()
        return append_OK

    def append(self, new_data) -> True:
        self.put_lock.acquire()
        add_ok = False
        try:
            tempdb = SiteTempDatabase(self.ref)
            try:
                #tempdb.cur.execute(u"INSERT INTO TEMP (LINK, RS_CODE, LEV, L_TYPE) "
                #                   u"VALUES (\'{0:s}\', {1:d}, {2:d}, {3:d});".format(new_data.link, new_data.response_code,
                #                                                                      new_data.link_level, new_data.link_type))
                tempdb.cur.execute("INSERT OR IGNORE INTO TEMP (LINK, RS_CODE, LEV, L_TYPE) "
                                   "VALUES (?, ?, ?, ?);", (new_data.link, new_data.response_code, new_data.link_level,
                                                            new_data.link_type))
                self.in_counter += 1
                tempdb.db.commit()
                tempdb.close()
                add_ok = True
            except Exception as ex:
                #print(ex)
                tempdb.close()
        except OperationalError as outer_ex:  # indicate if it has concurrent read write problem
            print(outer_ex)
        finally:
            self.put_lock.release()
            return add_ok

    def reset(self):
        self.output_c = 0
        self.temp_counter = 0
        SiteTempDatabase.force_clear(self.ref)
        self.set_continue_lock(True)

    def clear(self): # do not use this
        self.set_continue_lock(False)
        while not self.put_lock.acquire(False):
            time.sleep(0.1)
        while not self.get_lock.acquire(False):
            time.sleep(0.1)
        #while not self.rw_lock.acquire(False):
        #    time.sleep(0.1)
        print("database is stopped, and being cleared:", self.ref)
        SiteTempDatabase.force_clear(self.ref)
        self.put_lock.release()
        self.get_lock.release()
        #self.rw_lock.release()

    def __next__(self):
        """
        Get next object
        :return: tuple (The ref obj, the obj from database)
        """
        item = None
        output_obj = None
        while True:
            item = None
            with self.get_lock:
                tempdb = None
                try:
                    tempdb = SiteTempDatabase(self.ref)
                except OperationalError as ex:
                    print(ex)
                if not self.can_continue():
                    break
                if tempdb is not None:
                    try:
                        # cur = tempdb.cur.execute(u"SELECT * FROM TEMP "
                        #                         # u"WHERE RS_CODE==200 AND L_TYPE==2 " output all
                        #                          u"ORDER BY rowid LIMIT 1 OFFSET {0:d};".format(self.temp_counter,))
                        cur = tempdb.cur.execute(u"SELECT LINK, RS_CODE, LEV, L_TYPE FROM TEMP ORDER BY ID LIMIT 1 "
                                                 u"OFFSET {0:d};".format(self.temp_counter,))
                        item = cur.fetchone()
                        tempdb.close()
                    except:
                        pass

            if item is not None and len(item) > 0:
                link, rs_code, level, link_type = item
                # if link == self.last_output_record:
                #     continue
                # else:
                self.last_output_record = link
                output_obj = OnSiteLink(link, response_code=rs_code, link_level=level, link_type=link_type)

            update_time = time.time()
            if output_obj is not None:
                self.temp_counter += 1
                self.set_output_counter_plus()
                self._last_update_time = update_time
                break
            elif self.ref_obj is not None and self.ref_obj.is_idle():
                #if self.temp_counter >= self.all_record:
                    #print("has output all record", self.temp_counter)
                print(self.ref_obj.orginal_link, " ? worker is idle, break!")
                break
            elif update_time - self._last_update_time > self._get_timeout:
                print(self.ref_obj.orginal_link, " ? data source dried, break!")
                break

            time.sleep(self.output_f)

        if output_obj is not None:
            return self.ref_obj, output_obj
        else:
            self.set_continue_lock(False)
            raise StopIteration

    def get_next(self, link_tpye: int=OnSiteLink.TypeAll, response_code: int=ResponseCode.All):
        counter = 0
        while True:
            if not self.can_continue():
                # print("data source is set not to continue!")
                raise StopIteration

            item = None
            self.get_lock.acquire()
            try:
                tempdb = SiteTempDatabase(self.ref)
                cur = tempdb.cur.execute(u"SELECT LINK, RS_CODE, LEV, L_TYPE, rowid FROM TEMP "
                                         u"ORDER BY ID LIMIT 1 OFFSET {0:d};".format(counter,))
                item = cur.fetchone()
                tempdb.close()
            except Exception as ex:
                msg = "error in SiteTempDataDisk.get_next(), " + self.ref
                ErrorLogger.log_error("SiteTempDataDisk", ex, msg)
            finally:
                self.get_lock.release()

            output_obj = None
            if item is not None and len(item) > 0:
                counter += 1
                link = item[0]
                rs_code = item[1]
                level = item[2]
                inner_link_type = item[3]
                obj = OnSiteLink(link, response_code=rs_code, link_level=level, link_type=inner_link_type)
                #print("load: ", str(obj))
                if link_tpye == OnSiteLink.TypeAll or inner_link_type == link_tpye:
                    if response_code == ResponseCode.All:
                        output_obj = obj
                    elif response_code == ResponseCode.LinkNotBroken and not ResponseCode.is_link_broken(rs_code):
                        output_obj = obj
                    elif response_code == ResponseCode.LinkBroken and ResponseCode.is_link_broken(rs_code):
                        output_obj = obj
                    elif rs_code == response_code:
                        output_obj = obj
                    else:
                        continue
                else:
                    continue
            else:
                raise StopIteration
            if output_obj is not None:

                yield output_obj
            else:
                raise StopIteration

