from DomainFinderSrc.Utilities import FilePath
from DomainFinderSrc.MiniServer.DatabaseServer.SiteDB import CategoryDomainSiteDB, CatagoryDomainSiteDataStruct
from DomainFinderSrc.MiniServer.DatabaseServer.CategoryDB import *
from DomainFinderSrc.MiniServer.DatabaseServer.DBManager import DBManagerInterface
from threading import Event, RLock
from DomainFinderSrc.Utilities.Logging import ErrorLogger
from DomainFinderSrc.MiniServer.Common.SocketCommands import ServerState, MiningList, ServerCommand, CommandStruct
from DomainFinderSrc.Utilities.Serializable import Serializable, NamedMutableSequence
market_place_db_addr = FilePath.get_marketplace_db_path("MarketplaceSites.db")
market_place_skeleton_db_addr = FilePath.get_marketplace_db_path("MarketplaceSkeletonSites.db")


def db_update_process(skeleton_db_addr: str="", market_db_addr: str=""):
    if len(skeleton_db_addr) == 0:
        skeleton_db_addr = market_place_skeleton_db_addr
    if len(market_db_addr) == 0:
        market_db_addr = market_place_db_addr
    skeleton_db_manager = CategoryDBManager(skeleton_db_addr)
    skeleton_db_manager.reset_category_count()
    len_per_patch = 20000
    db = CategoryDomainSiteDB(market_db_addr)
    site_count = db.site_count(False)
    current_count = 0
    while current_count < site_count:
        sites = db.get_next_patch_no_rollover(current_count, len_per_patch)
        for site in sites:
            if isinstance(site, CatagoryDomainSiteDataStruct):
                for topic in site.get_categories():
                    sub_category = skeleton_db_manager.get_sub_category(CategoryManager.decode_sub_category(topic, False))
                    sub_category.count += 1
                current_count += 1
    skeleton_db_manager.re_calculate_stats()
    skeleton_db_manager.save()


class MarketplaceRequst(NamedMutableSequence):
    # __slots__ = ("tf", "cf", "da", "date", "topics", "topic_s", "price", "rate", "domain_id",)
    __slots__ = tuple(list(CategoryDomainSiteDB.get_fields_names()) + ["INDEX", "LEN"])


class MarketplaceDBManager(DBManagerInterface):
    def __init__(self, *args, **kwargs):
        update_process = kwargs.get("update_process", None)
        if update_process is None:
            kwargs.update({"update_process": db_update_process})
        DBManagerInterface.__init__(self, *args, **kwargs)

    def get_update_process_args(self) -> dict:
        return {"skeleton_db_addr": self._skeleton_db_addr, "market_db_addr": self._db_addr}

    def get_db_data(self, index=0, count=0, reverse_read=False, **kwargs) -> MiningList:
        return_data = MiningList("Data")
        if index >= 0 and count > 0:
            with self._db_lock:
                db = CategoryDomainSiteDB(self._db_addr)
                return_data.data = db.get_next_patch_no_rollover(index=index, count=count, reverse_read=reverse_read, **kwargs)
                db.close()
        return return_data

    def add_db_data(self, data=None, **kwargs) -> bool:
        success = False
        try:
            if isinstance(data, MiningList):
                with self._db_lock:
                    db = CategoryDomainSiteDB(self._db_addr)
                    db.add_sites(data.data)
                    db.close()
                    success = True
            else:
                raise ValueError("input value has incorrect type.")
        except Exception as ex:
            ErrorLogger.log_error("MarketplaceDBManager.add_db_data", ex)
        finally:
            return success

    def update_db_data(self, data=None, **kwargs) -> bool:
        return self.add_db_data(data, **kwargs)

    def delete_db_data(self, data=None, **kwargs) -> bool:
        success = False
        try:
            if isinstance(data, MiningList):
                with self._db_lock:
                    db = CategoryDomainSiteDB(self._db_addr)
                    db.delete_sites(data.data)
                    db.close()
                    success = True
        except Exception as ex:
            ErrorLogger.log_error("MarketplaceDBManager.delete_db_data", ex)
        finally:
            return success

    def handle_request(self, cmd: CommandStruct) -> Serializable or bool:
        data = cmd.data
        code = cmd.cmd
        if code == ServerCommand.Com_Get_DB_DATA and isinstance(data, MarketplaceRequst):  # outgoing data
            # parameters = {}
            # tf = data.TF if isinstance(data.TF, int) else 0
            # cf = data.CF if isinstance(data.CF, int) else 0
            # da = data.DA if isinstance(data.DA, int) else 0
            # topics = data.topics if isinstance(data.topics, str) else ""
            # topic_s = data.topic_s if isinstance(data.topic_s, int) else 0
            # price = data.price if isinstance(data.price, float) else 0.0
            # date = data.date if isinstance(data.date, int) else 0
            # rate = data.rate if isinstance(data.rate, int) else 0
            # domain_id = data.domain_id if isinstance(data.domain_id, "") else ""
            parameters = data.get_non_none_parameters()
            index = parameters.get("INDEX", 0)
            data_len = parameters.get("LEN", 100)
            return self.get_db_data(index, data_len, reverse_read=False, **parameters)
        else:
            return DBManagerInterface.handle_request(self, cmd=cmd)
