from DomainFinderSrc.Scrapers.SiteTempDataSrc.SiteTempDataSrcInterface import *


class SiteTempDataMem(SiteTempDataSrcInterface):
    def __init__(self, ref: str, data, ref_obj: SiteTempDataSrcRefInterface=None):
        super(SiteTempDataMem, self).__init__(ref, data, ref_obj)
        self.page_list = []
        self.in_counter = 0
        self.temp_counter = 0

    def count_all(self):
        return self.in_counter
    
    def get_all_outbound_links(self, response_code: int=ResponseCode.LinkBroken) ->[]:
        """
        :return: a list of domain in SiteChecker.OnSiteLink object
        """
        if response_code == ResponseCode.All:
            return [x for x in self.page_list if x.link_type == OnSiteLink.TypeOutbound]
        elif response_code == ResponseCode.LinkNotBroken:
            return [x for x in self.page_list if x.link_type == OnSiteLink.TypeOutbound and not ResponseCode.is_link_broken(x.response_code)]
        elif response_code == ResponseCode.LinkBroken:
            return [x for x in self.page_list if x.link_type == OnSiteLink.TypeOutbound and ResponseCode.is_link_broken(x.response_code)]
        else:
            return [x for x in self.page_list if x.link_type == OnSiteLink.TypeOutbound and x.response_code == response_code]

    def get_onsite_links(self, level: int, response_code: int) -> []:
        """
        :param level: the level where the link was in the domain
        :return: a list of OnSiteLink
        :exception: ValueError if level is < 0
        """
        if level < 0:
            raise ValueError()
        else:
            if response_code == ResponseCode.All:
                return [x for x in self.page_list if x.link_type == OnSiteLink.TypeOnSite and
                        x.link_level == level and x.response_code == response_code]
            elif response_code == ResponseCode.LinkNotBroken:
                return [x for x in self.page_list if x.link_type == OnSiteLink.TypeOnSite and
                        x.link_level == level and not ResponseCode.is_link_broken(x.response_code)]
            elif response_code == ResponseCode.LinkBroken:
                return [x for x in self.page_list if x.link_type == OnSiteLink.TypeOnSite and
                        x.link_level == level and ResponseCode.is_link_broken(x.response_code)]
            else:
                return [x for x in self.page_list if x.link_type == OnSiteLink.TypeOnSite and
                        x.link_level == level and x.response_code == response_code]

    def is_link_in_page_list(self, link: str):
        if link is None:
            raise ValueError()
        result = next((x for x in self.page_list if x.link == link), None)
        if result is None:
            return False
        else:
            return True

    def append(self, new_data):
        add_ok = False
        self.put_lock.acquire()
        if new_data is not None:
            if not self.is_link_in_page_list(new_data.link):
                self.in_counter += 1
                self.page_list.append(new_data)
                add_ok = True
            else:
                add_ok = False
        else:
            add_ok = False
        self.put_lock.release()
        return add_ok

    def reset(self):
        self.temp_counter = 0

    def clear(self):
        self.page_list.clear()

    def get_next(self, link_tpye: int=OnSiteLink.TypeAll, response_code: int=ResponseCode.All):
        while self.can_continue():
            item = None
            self.get_lock.acquire()
            try:
                item = self.page_list[self.temp_counter]
            except:
                break
            self.get_lock.release()
            output_obj = None
            if item is not None:
                self.temp_counter += 1
                if link_tpye == OnSiteLink.TypeAll or item.link_type == link_tpye:
                    if response_code == ResponseCode.All:
                        output_obj = item
                    elif response_code == ResponseCode.LinkNotBroken and not ResponseCode.is_link_broken(item.response_code):
                        output_obj = item
                    elif response_code == ResponseCode.LinkBroken and ResponseCode.is_link_broken(item.response_code):
                        output_obj = item
                    elif item.response_code == response_code:
                        output_obj = item
                    else:
                        continue
                else:
                    continue
            update_time = time.time()
            if output_obj is not None:
                self.set_output_counter_plus()
                self._last_update_time = update_time
                yield output_obj
            elif update_time - self._last_update_time > self._get_timeout:
                print("data source dried, break!")
                self.set_continue_lock(False)
                break
        return