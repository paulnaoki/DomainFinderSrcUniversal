from DomainFinderSrc.Scrapers.LinkChecker import ResponseCode
import threading
import time
import base64


class OnSiteLink:
    TypeAll = 0
    TypeOutbound = 1
    TypeOnSite = 2

    def __init__(self, link: str, response_code: int, link_level=0, link_type=TypeOnSite):
        self.link = link
        self.response_code = response_code
        self.link_level = link_level
        self.link_type = link_type

    def __str__(self):
        if self.link_type == OnSiteLink.TypeOnSite:
            return self.link + " in-site   level: " + str(self.link_level) + " code: " + str(self.response_code)
        else:
            return self.link + " outbound   level: " + str(self.link_level) + " code: " + str(self.response_code)

    def __cmp__(self, other):
        if self.link == other.link:
            return True
        else:
            return False


class SiteTempDataSrcRefInterface:
    def is_idle(self):
        raise NotImplementedError

    def get_internal_page_progress_index(self) -> int:
        raise NotImplementedError

    def set_internal_page_progress_index(self, index: int):
        raise NotImplementedError


class SiteTempDataSrcInterface(object):

    @staticmethod
    def get_valid_file_name(ref: str)->str:
        #file_name_string = ref.encode('utf-7')
        file_name_string = base64.b64encode(ref.encode('utf-8'))
        temp = str(file_name_string, 'utf-8').replace("/", "+")
        if len(temp) > 200:
            return temp[0:199]
        else:
            return temp

    def __init__(self, ref: str, data=None, ref_obj: SiteTempDataSrcRefInterface=None):
        self.ref = SiteTempDataSrcInterface.get_valid_file_name(ref)
        self.ref_obj = ref_obj
        if data is not None:
            if isinstance(data, type([])) and len(data) > 0:
                for item in data:
                    self.append(item)
            else:
                self.append(data)
        self.continue_output = True
        self.put_lock = threading.RLock()
        self.get_lock = threading.RLock()
        self.rw_lock = threading.RLock()
        self.continue_lock = threading.RLock()
        self.output_c_lock = threading.RLock()
        self.output_c = 0
        self.in_counter = 0
        self.temp_counter = 0
        #the following used in get_next()
        self._get_timeout = 12000  # if getting result after this number of second failed, terminate output
        self._last_update_time = time.time()
        self.all_record = 0

    def set_progress(self, progress: int):
        self.temp_counter = progress

    def __next__(self):  # iterator method
        pass

    def __iter__(self):
        return self

    def set_output_counter_plus(self):
        self.output_c_lock.acquire()
        self.output_c += 1
        self.output_c_lock.release()

    def get_output_counter(self):
        self.output_c_lock.acquire()
        output_c = self.output_c
        self.output_c_lock.release()
        return output_c

    def set_continue_lock(self, can_contiune=True):
        with self.continue_lock:
            self.continue_output = can_contiune

    def can_continue(self):
        with self.continue_lock:
            contin = self.continue_output
        return contin

    def count_all(self):
        return 0

    def count_onsite_links(self):
        return 0

    def get_all_outbound_links(self, response_code: int=ResponseCode.LinkBroken) ->[]:
        pass

    def get_onsite_links(self, level: int, response_code: int) -> []:
        pass

    def is_link_in_page_list(self, link: str) -> True:
        pass

    def append_many(self, new_data_list, convert_tuple=True) -> bool:
        pass

    def append(self, new_data):
        """
        add a new data to the database, return true if added sucessfully, else return false
        :param new_data:
        :return:
        """
        pass

    def append_many_if_not_exist(self, new_data_list:[]) -> (int, []):
        pass

    def reset(self):
        pass

    def clear(self):
        pass

    def additional_startup_procedures(self):
        """
        call this method if subclass has more additional steps to follow
        :return:
        """
        pass

    def additional_finish_procedures(self):
        pass

    def re_target(self, ref: str, data):
        #self.ref = SiteTempDataSrcInterface.get_valid_file_name(ref)
        self.reset()
        if data is not None:
            if isinstance(data, type([])) and len(data) > 0:
                self.append_many(data)
                # for item in data:
                #     self.append(item)
            else:
                self.append_many([data])
        self.continue_output = True

    def get_next(self, link_tpye: int=OnSiteLink.TypeAll, response_code: int=ResponseCode.All):
        pass


class SiteInfo:
    def __init__(self, domain: str, data_source: SiteTempDataSrcInterface):
        self.domain = domain
        if data_source is not None:
            self.data_source = data_source
            self.total_links_count = data_source.count_all()
            self.internal_link_count = data_source.count_onsite_links()
            self.external_link_count = self.total_links_count - self.internal_link_count
            self.external_link_error = 0
            self.internal_link_error = 0

            # for page in self.data_source.get_next():
            #     if page.link_type == OnSiteLink.TypeOnSite:
            #         self.internal_link_count += 1
            #         if ResponseCode.is_link_broken(page.response_code):
            #             self.internal_link_error += 1
            #     else:
            #         self.external_link_count += 1
            #         if ResponseCode.is_link_broken(page.response_code):
            #             self.internal_link_error += 1

    def get_details(self)->(int, int, int, int, int, str):
        """
        get all stats about a site
        :return:(total_links_count, external_link_count, external_link_error, internal_link_count, internal_link_error \
                 domain name in str)
        """
        return self.total_links_count, self.external_link_count, self.external_link_error, self.internal_link_count,\
            self.internal_link_error, self.domain

    def __str__(self):
        return "%s total: %i, internal: %i, external: %i, internal e: %i, external e: %i" % (self.domain,
                                                                                             self.total_links_count,
                                                                                             self.internal_link_count,
                                                                                             self.external_link_count,
                                                                                             self.internal_link_error,
                                                                                             self.external_link_error)