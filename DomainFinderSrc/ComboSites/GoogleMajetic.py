from DomainFinderSrc.MajesticCom import MajesticCom
from DomainFinderSrc.MajesticCom.DataStruct import MajesticBacklinkDataStruct
from DomainFinderSrc.GoogleCom import GoogleCom
from DomainFinderSrc.Scrapers.LinkChecker import LinkChecker


class GoogleMajestic:

    @staticmethod
    def get_sites_by_seed_sites(account: MajesticCom, seed_domains: [], topic="", fresh_data=False, index=0,
                                iteration=1, loop_count=0, count_per_domain=100, callback=None) -> []:
        if iteration < 0:
            raise ValueError("get_sites_by_seed_sites: iteration should >= 0.")
        sub_domains = [LinkChecker.get_root_domain(x, use_www=False)[4] for x in seed_domains[index:]]
        if len(sub_domains) == 0:
            return []
        backlinks = []
        # counter = index
        temp_sub_domains = []
        temp = []
        for sub_domain in sub_domains:
            try:
                temp = account.get_backlinks(sub_domain, count_per_domain, topic=topic, is_dev=False,
                                             fresh_data=fresh_data)
            except Exception as ex:
                print(ex)
            print("doing backlinks of domain:", sub_domain)
            for item in temp:
                if isinstance(item, MajesticBacklinkDataStruct):
                    domain = LinkChecker.get_root_domain(item.backlink, use_www=False)[4]
                    if domain not in sub_domains and domain not in temp_sub_domains:
                        temp_sub_domains.append(domain)
                        # counter += 1
                        item.ref_domain = domain
                        backlinks.append(item)
                        if callback is not None:
                            callback(item)
        if loop_count >= iteration:
            return backlinks
        else:
            return backlinks + GoogleMajestic.get_sites_by_seed_sites(account, sub_domains + temp_sub_domains, topic, fresh_data, len(seed_domains),
                                                                      iteration, loop_count+1, count_per_domain, callback)
