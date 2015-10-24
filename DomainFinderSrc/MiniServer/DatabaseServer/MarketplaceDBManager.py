from DomainFinderSrc.Utilities import FilePath
from DomainFinderSrc.MiniServer.DatabaseServer.SiteDB import CategoryDomainSiteDB, CatagoryDomainSiteDataStruct
from DomainFinderSrc.MiniServer.DatabaseServer.CategoryDB import *
from DomainFinderSrc.MiniServer.Common.SocketCommands import ServerState, MiningList
from DomainFinderSrc.MiniServer.DatabaseServer.DBManager import DBManagerInterface


market_place_db_addr = FilePath.get_marketplace_db_path("MarketPlaceDB.db")
market_place_skeleton_db_addr = FilePath.get_marketplace_db_path("MarketPlaceSkeletonDB.db")


def db_update_process():
    skeleton_db_manager = CategoryDBManager(market_place_skeleton_db_addr)
    skeleton_db_manager.reset_category_count()
    len_per_patch = 20000
    db = CategoryDomainSiteDB(market_place_db_addr)
    site_count = db.site_count(False)
    current_count = 0
    while current_count < site_count:
        sites = db.get_next_patch_no_rollover(current_count, len_per_patch)
        for site in sites:
            if isinstance(site, CatagoryDomainSiteDataStruct):
                for topic in site.get_categories():
                    sub_category = skeleton_db_manager.get_sub_category(CategoryManager.decode_sub_category(topic))
                    sub_category.count += 1
                current_count += 1
    skeleton_db_manager.re_calculate_stats()
    skeleton_db_manager.save()


class MarketplaceDBManager(DBManagerInterface):
    def __init__(self, update_time_hour: int=24):
        DBManagerInterface.__init__(self, update_time_hour=update_time_hour, update_process=db_update_process,
                                    db_addr=market_place_db_addr, skeleton_db_addr=market_place_skeleton_db_addr)

    def get_db_data(self, index=0, count=0, **kwargs) -> MiningList:
        return_data = MiningList("Data")
        if index >= 0 and count > 0:
            with self._db_lock:
                db = CategoryDomainSiteDB(self._db_addr)
                return_data.data = db.get_next_patch_no_rollover(index=index, count=count, **kwargs)
                db.close()
        return return_data

    def add_db_data(self, data=None, **kwargs):
        if isinstance(data, MiningList):
            with self._db_lock:
                db = CategoryDomainSiteDB(self._db_addr)
                db.add_sites(data.data)
                db.close()

    def update_db_data(self, data=None, **kwargs):
        self.add_db_data(data, **kwargs)

    def delete_db_data(self, data=None, **kwargs):
        if isinstance(data, MiningList):
            with self._db_lock:
                db = CategoryDomainSiteDB(self._db_addr)
                db.delete_sites(data.data)
                db.close()