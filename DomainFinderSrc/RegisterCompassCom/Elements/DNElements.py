from DomainFinderSrc.PageNavigator import SelecElement


class DNElements:
    keywordField = 1

    @staticmethod
    def get_element_id(id)->SelecElement:
        return {
            DNElements.keywordField: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_txt_keyword'),
        }.get(id, None)
