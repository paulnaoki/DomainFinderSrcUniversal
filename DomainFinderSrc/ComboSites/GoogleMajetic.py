from DomainFinderSrc.MajesticCom import MajesticCom
from DomainFinderSrc.MajesticCom.DataStruct import MajesticBacklinkDataStruct, MajesticRefDomainStruct
from DomainFinderSrc.GoogleCom import GoogleCom
from DomainFinderSrc.Scrapers.LinkChecker import LinkChecker
from DomainFinderSrc.MajesticCom.Category import *
from multiprocessing.pool import ThreadPool
import time
from multiprocessing import Process, Queue


class GoogleMajestic:

    @staticmethod
    def _get_back_link_thread(account: MajesticCom, sub_domain: str, count_per_domain: int, fresh_data: bool,
                              sub_domains: [], temp_sub_domains: [], categories: [], callback, tf=20, bad_country_list=[]):
        temp = []
        print("doing backlinks of domain:", sub_domain, " domain len:", len(temp_sub_domains))
        try:

            temp = account.get_backlinks(sub_domain, count_per_domain, topic="", is_dev=False, fresh_data=fresh_data)
        except Exception as ex:
            print(ex)
        for item in temp:
            if isinstance(item, MajesticBacklinkDataStruct):

                # item_catagory = str(CategoryManager.decode_sub_category(item.src_topic, False))
                domain = LinkChecker.get_root_domain(item.backlink, use_www=False)[4]
                item.ref_domain = domain
                # if callback is not None:
                #     callback(item)
                # if len(target_catagories) > 0 and item_catagory not in target_catagories:
                #         continue
                if domain not in sub_domains and domain not in temp_sub_domains:
                    if len(categories) > 0:
                        is_in = False
                        if len(item.src_topic) > 0:
                            decoded = str(CategoryManager.decode_sub_category(item.src_topic, False))
                            for cate in categories:
                                if cate in decoded:
                                    is_in = True
                                    break
                            if is_in and item.src_tf >= tf:
                                temp_sub_domains.append(domain)
                    elif item.src_tf >= tf:
                        temp_sub_domains.append(domain)
                    item.ref_domain = domain
                    if callback is not None:
                        callback(item)
        time.sleep(1)

    @staticmethod
    def _get_ref_domain_thread(account: MajesticCom, sub_domain: str, count_per_domain: int, fresh_data: bool,
                               sub_domains: [], temp_sub_domains: [], categories: [], callback, tf=20, bad_country_list=[]):
        temp = []
        print("doing backlinks of domain:", sub_domain, " domain len:", len(temp_sub_domains))
        try:
            temp = account.get_ref_domains(sub_domain, max_count=count_per_domain, is_dev=False, fresh_data=fresh_data)
            # temp = account.get_backlinks(sub_domain, count_per_domain, topic="", is_dev=False, fresh_data=fresh_data)
        except Exception as ex:
            print(ex)
        for item in temp:
            if isinstance(item, MajesticRefDomainStruct):

                # item_catagory = str(CategoryManager.decode_sub_category(item.src_topic, False))
                domain = item.domain
                item.ref_domain = domain
                if domain not in sub_domains and domain not in temp_sub_domains:
                    if len(categories) > 0:
                        is_in = False
                        if len(item.src_topic) > 0:
                            decoded = str(CategoryManager.decode_sub_category(item.src_topic, False))
                            for cate in categories:
                                if cate in decoded:
                                    is_in = True
                                    break
                            if is_in and item.tf >= tf and item.country not in bad_country_list:  # add seed
                                temp_sub_domains.append(domain)
                    elif item.tf >= tf and item.country not in bad_country_list:
                        temp_sub_domains.append(domain)
                    item.ref_domain = domain
                    if callback is not None:
                        callback(item)
        time.sleep(1)

    @staticmethod
    def get_sites_by_seed_sites_muti_threads(account: MajesticCom, seed_domains: [], catagories: [], fresh_data=False, index=0,
                                iteration=1, loop_count=0, count_per_domain=100, callback=None, current_count=0,
                                max_count=-1, tf=20, thread_pool_size=20, get_backlinks=True, bad_country_list=[]):
        """

        :param account:
        :param seed_domains:
        :param catagories:
        :param fresh_data:
        :param index:
        :param iteration:
        :param loop_count:
        :param count_per_domain:
        :param callback:
        :param current_count:
        :param max_count:
        :param tf:
        :param thread_pool_size:
        :param get_backlinks: it will get backlinks of domains if True, else it will get ref domains instead, which is cheaper.
        :return:
        """
        target_func = GoogleMajestic._get_back_link_thread if get_backlinks else GoogleMajestic._get_ref_domain_thread
        if iteration < 0:
            raise ValueError("get_sites_by_seed_sites: iteration should >= 0.")
        sub_domains = [LinkChecker.get_root_domain(x, use_www=False)[4] for x in seed_domains[index:]]
        if len(sub_domains) == 0:
            print("sub_domains is len 0.")
            return
        # counter = index
        process_len = len(sub_domains)
        if max_count > 0:
            if current_count >= max_count:
                print("exceeded seed len.")
                return
            elif current_count + process_len > max_count:
                process_len = max_count - current_count
        #target_catagories = []
        # for catagory in catagories:
        #     target_catagories.append(str(CategoryManager.decode_sub_category(catagory, False)))
        temp_sub_domains = []

        thread_pool = ThreadPool(processes=thread_pool_size)
        processes = [thread_pool.apply_async(target_func,
                                             args=(account, x, count_per_domain, fresh_data, sub_domains,
                                                   temp_sub_domains, catagories,  callback, tf, bad_country_list))
                     for x in sub_domains[0: process_len]]
        results = [y.get() for y in processes]
        thread_pool.terminate()
        current_count += process_len
        if loop_count >= iteration:
            return
        else:
            new_seeds = sub_domains + temp_sub_domains
            print("going to next level with seeds:", len(new_seeds))
            return GoogleMajestic.get_sites_by_seed_sites_muti_threads(account, new_seeds,
                                                                       catagories, fresh_data, len(seed_domains),
                                                                       iteration, loop_count+1, count_per_domain,
                                                                       callback, current_count, max_count,
                                                                       thread_pool_size=10, tf=tf,
                                                                       get_backlinks=get_backlinks,
                                                                       bad_country_list=bad_country_list)

    @staticmethod
    def get_sites_by_seed_sites(account: MajesticCom, seed_domains: [], catagories: [], fresh_data=False, index=0,
                                iteration=1, loop_count=0, count_per_domain=100, callback=None, current_count=0,
                                max_count=-1, tf=20) -> []:
        if iteration < 0:
            raise ValueError("get_sites_by_seed_sites: iteration should >= 0.")
        sub_domains = [LinkChecker.get_root_domain(x, use_www=False)[4] for x in seed_domains[index:]]
        if len(sub_domains) == 0:
            return []
        backlinks = []
        # counter = index
        if max_count > 0 and current_count >= max_count:
                return backlinks
        temp_sub_domains = []
        temp = []
        # target_catagories = []
        # for catagory in catagories:
        #     target_catagories.append(str(CategoryManager.decode_sub_category(catagory, False)))
        for sub_domain in sub_domains:
            print("doing backlinks of domain:", sub_domain, "seed len:", len(temp_sub_domains))
            try:
                temp = account.get_backlinks(sub_domain, count_per_domain, topic="", is_dev=False,
                                             fresh_data=fresh_data)
                current_count += 1
            except Exception as ex:
                print(ex)
            for item in temp:
                if isinstance(item, MajesticBacklinkDataStruct):

                    # item_catagory = str(CategoryManager.decode_sub_category(item.src_topic, False))
                    domain = LinkChecker.get_root_domain(item.backlink, use_www=False)[4]
                    item.ref_domain = domain
                    # if callback is not None:
                    #     callback(item)
                    # if len(target_catagories) > 0 and item_catagory not in target_catagories:
                    #         continue
                    if domain not in sub_domains and domain not in temp_sub_domains:
                        if len(catagories) > 0:
                            is_in = False
                            if len(item.src_topic) > 0:
                                decoded = str(CategoryManager.decode_sub_category(item.src_topic, False))
                                for cate in catagories:
                                    if cate in decoded:
                                        is_in = True
                                        break
                                if is_in and item.src_tf >= tf:
                                    temp_sub_domains.append(domain)
                        elif item.src_tf >= tf:
                            temp_sub_domains.append(domain)
                        item.ref_domain = domain
                        if callback is not None:
                            callback(item)

            if max_count > 0 and current_count >= max_count:
                break
        if loop_count >= iteration:
            return backlinks
        else:
            return backlinks + GoogleMajestic.get_sites_by_seed_sites(account, sub_domains + temp_sub_domains, catagories, fresh_data, len(seed_domains),
                                                                      iteration, loop_count+1, count_per_domain, callback, current_count, max_count, tf)
