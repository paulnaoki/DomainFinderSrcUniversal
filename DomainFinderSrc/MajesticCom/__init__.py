import urllib.parse
import requests
from DomainFinderSrc.MajesticCom.DataStruct import MajesticComStruct, MajesticRefDomainStruct, \
    MajesticBacklinkDataStruct
from DomainFinderSrc.SiteConst import SiteAccount


class MajesticConst:
    Live_endpoint = "http://api.majestic.com/api/json?"
    Deve_endpoint = "http://developer.majestic.com/api/json?"
    cmd_get_index_item_info = "GetIndexItemInfo"
    cmd_get_ref_domains = "GetRefDomains"   # ref domains info
    cmd_get_anchor_text = "GetAnchorText"  # anchor text and no follow backlinks count for each anchor text
    cmd_get_backlinks = "GetBackLinkData"


class MajesticCom:
    def __init__(self, account: SiteAccount):
        self.account = account

    @staticmethod
    def _get_json_data(parameters: dict, is_dev=True):
        para_encoded = urllib.parse.urlencode(parameters)
        if is_dev:
            request_url = MajesticConst.Deve_endpoint + para_encoded
        else:
            request_url = MajesticConst.Live_endpoint + para_encoded
        return requests.get(request_url).json()

    def get_backlinks(self, domain: str, max_count=10, topic="", is_dev=True, fresh_data=False) -> []:
        """
        get backlinks information about a domain.
        http://developer-support.majestic.com/api/commands/get-back-link-data.shtml
        :param domain: domain name, could be a link.
        :param max_count: number of backlinks result points.
        :param is_dev: dev mode for test on fake data set, else for production mode.
        :return:
        """
        if len(domain) == 0:
            raise ValueError("get_backlinks(): domain name is empty")
        if max_count > 50000:
            raise ValueError("get_backlinks(): number of backlinks exceed majestic limit, should be 50000, currently "
                             + str(max_count))
        parameters = {
            # "datasource": "fresh",
            "app_api_key": self.account.APIKey,
            "cmd": MajesticConst.cmd_get_backlinks,
            "item": domain,
            "Count": max_count,
            # "Mode": 1,
            "MaxSourceURLsPerRefDomain": 1,  #  If set to 1, then it will effectively produce list of referring domains with just 1 best backlink from each of them.
            "MaxSameSourceURLs": 1,  # If set to 1 it will guarantee that only unique source urls returned.
        }
        if fresh_data:
            parameters.update({"datasource": "fresh"})
        if len(topic) > 0:
            parameters.update({#"ShowDomainInfo": 1,
                               "FilterTopic": topic,
                               #"FilterTopicsRefDomainsMode": 1  # This should be used in conjunction with
                               # ShowDomainInfo=1 as the link itself may not be of the supplied FilterTopic
                               # but it’s domain will (it may not be the primary topic)
                               })
        json_data = MajesticCom._get_json_data(parameters, is_dev)
        if json_data["Code"] == "OK":
            backlinks = []
            table = json_data["DataTables"]["BackLinks"]["Data"]
            for item in table:
                backlink = item["SourceURL"]
                src_tf = item["SourceTrustFlow"]
                src_cf = item["SourceCitationFlow"]
                structed = MajesticBacklinkDataStruct(backlink=backlink, src_tf=src_tf, src_cf=src_cf)
                # if len(topic) > 0:
                topic_count = 3
                default_topic = ""
                default_topic_tf = 0
                for i in range(0, topic_count):
                    try:
                        src_topic_temp = item["TargetTopicalTrustFlow_Topic_{0:d}".format(i,)]
                        src_topic_tf_temp = item["TargetTopicalTrustFlow_Value_{0:d}".format(i,)]
                        if i == 0:
                            default_topic = src_topic_temp
                            default_topic_tf = src_topic_tf_temp
                        if src_topic_temp == topic:
                            structed.src_topic = src_topic_temp
                            structed.src_topic_tf = src_topic_tf_temp
                    except:
                        break
                if len(structed.src_topic) == 0:
                    structed.src_topic = default_topic
                    structed.src_topic_tf = default_topic_tf

                backlinks.append(structed)
            return backlinks
        else:
            raise ValueError("get_backlinks(): data request reuturn wrong.",)

    def get_ref_domains(self, domain: str, max_count=10, is_dev=True, fresh_data=False) ->[]:
        """
        get referring domains information about a domain.
        :param domain: domain name, could be a link.
        :param max_count: number of anchor text result points.
        :param is_dev: dev mode for test on fake data set, else for production mode.
        :return:list -> list of ref domains info in MajesticRefDomainStruct format
        """
        if len(domain) == 0:
            raise ValueError("get_ref_domains(): domain name is empty")
        parameters = {
            # "datasource": "fresh",
            "app_api_key": self.account.APIKey,
            "cmd": MajesticConst.cmd_get_ref_domains,
            "OrderBy1": 1,  # AlexaRank (lowest number means higher traffic)
            "OrderDir1": 0,  # ascending order for AlexaRank
            "OrderBy2": 2,  # number of referring root domains linking to a root domain.
            "OrderDir2": 1,  # descending order for referring domains
            "AnalysisDepth": 100000,  # (default) - no filter on anchor text
            "Count": max_count,
            "item0": domain,
        }
        if fresh_data:
            parameters.update({"datasource": "fresh"})
        json_data = MajesticCom._get_json_data(parameters, is_dev)
        if json_data["Code"] == "OK":
            ref_domains = []
            table = json_data["DataTables"]["Results"]["Data"]
            for item in table:
                ref_domains.append(MajesticRefDomainStruct(domain=item["Domain"], tf=item["TrustFlow"],
                                                           cf=item["CitationFlow"], backlinks=item["ExtBackLinks"],
                                                           country=item["CountryCode"], ref_domains=item["RefDomains"],
                                                           ip=item["IP"], alexa_rank=item["AlexaRank"]))
            return ref_domains
        else:
            raise ValueError("get_ref_domains(): data request reuturn wrong.",)

    def get_anchor_text_info(self, domain: str, max_count=10, is_dev=True, fresh_data=False) -> ([], int, int, int):
        """
        get anchor text information about a domain.
        :param domain: domain name, could be a link.
        :param max_count: number of anchor text result points.
        :param is_dev: dev mode for test on fake data set, else for production mode.
        :return:tuple -> list of anchor text, total backlinks, deleted backlinks, no-follow backlinks.
        """
        if len(domain) == 0:
            raise ValueError("get_anchor_text(): domain name is empty")
        parameters = {
            # "datasource": "fresh",
            "app_api_key": self.account.APIKey,
            "cmd": MajesticConst.cmd_get_anchor_text,
            "Mode": 0,  # (default) - returns aggregated anchor text stats.
            "TextMode": 0,  # (default) - returns anchor text (forced to lower case) as it was found with all punctunation marks etc
            "Count": max_count,
            "item": domain,
        }
        if fresh_data:
            parameters.update({"datasource": "fresh"})
        json_data = MajesticCom._get_json_data(parameters, is_dev)
        if json_data["Code"] == "OK":
            anchorTextRows = []
            anchorTexts = []
            total_links = 0
            deleted_links = 0
            no_follow_links = 0
            table = json_data["DataTables"]["AnchorText"]["Data"]
            for item in table:
                temp_anchor = str(item["AnchorText"]).lower()
                if temp_anchor not in anchorTexts:
                    anchorTexts.append(temp_anchor)
                total_links += item["TotalLinks"]
                deleted_links += item["DeletedLinks"]
                no_follow_links += item["NoFollowLinks"]
                anchorTextRows.append((temp_anchor, item["TotalLinks"], item["DeletedLinks"], item["NoFollowLinks"]))
            anchorTexts = [x for x in sorted(anchorTextRows, key=lambda anchorRow: anchorRow[1], reverse=True)]
            return anchorTexts, total_links, deleted_links, no_follow_links
        else:
            raise ValueError("get_anchor_text(): data request reuturn wrong.",)

    def get_cf_tf_list(self, domain_list: [], is_dev=True) ->[]:
        item_count = len(domain_list)
        if domain_list is None or item_count < 1:
            return None
        else:
            topic_count = 3
            item_count = len(domain_list)
            parameters = {"datasource": "fresh",
                          "DesiredTopics": topic_count,
                          "app_api_key": self.account.APIKey,
                          "cmd": MajesticConst.cmd_get_index_item_info,
                          "items": item_count,
                          "EnableResourceUnitFailover": 1,
            }
            for i in range(0, item_count):
                parameters["item"+str(i)] = domain_list[i]
            json_data = MajesticCom._get_json_data(parameters, is_dev)
            #json_data = json.loads(majectic_result)
            if json_data["Code"] == "OK":
                return_table = []
                table = json_data["DataTables"]["Results"]["Data"]
                for item in table:
                    topic = ""
                    for i in range(0, topic_count):
                        try:
                            temp = item["TopicalTrustFlow_Topic_{0:d}".format(i,)]
                            topic_trust_flow = item["TopicalTrustFlow_Value_{0:d}".format(i,)]
                            if temp is not None:
                                topic += temp + ":" + str(topic_trust_flow) + ";"
                        except:
                            pass
                    if item["ResultCode"] == "OK":
                        return_table.append(MajesticComStruct(domain=item["Item"], tf=item["TrustFlow"],
                                                           cf=item["CitationFlow"], ref_domains=item["RefDomains"],
                                                           backlinks=item["ExtBackLinks"],
                                                           topic=topic))
                    else:
                        raise ValueError("get_cf_tf_list(): data request reuturn wrong.", domain_list)
                return return_table
            else:
                raise ValueError("get_cf_tf_list(): data request reuturn wrong.", domain_list)


