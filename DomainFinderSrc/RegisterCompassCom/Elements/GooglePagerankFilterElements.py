from DomainFinderSrc.PageNavigator import SelecElement


class GPageRankFilterElement:
    PageGreater = 1
    PageEqual = 2
    PageLesser = 3
    PageLimit = 4
    NoPageRank = 5
    PagerankValid = 6
    PagerankMayValid = 7
    PagerankFaked = 8

    @staticmethod
    def get_element_id(element)->SelecElement:
        return {
            GPageRankFilterElement.PageGreater: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_ddl_compare_pr'), # <option> value = 2
            GPageRankFilterElement.PageEqual: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_ddl_compare_pr'), # <option> value = 1
            GPageRankFilterElement.PageLesser: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_ddl_compare_pr'), # <option> value = 0
            GPageRankFilterElement.PageLimit: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_txt_pagerank'), # a number
            GPageRankFilterElement.NoPageRank: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_chk_no_pr'),
            GPageRankFilterElement.PagerankValid: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_chk_valid'),
            GPageRankFilterElement.PagerankMayValid: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_chk_unknown'),
            GPageRankFilterElement.PagerankFaked: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_chk_invalid'),

        }.get(element, None)
