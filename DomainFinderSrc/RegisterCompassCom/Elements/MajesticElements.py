from DomainFinderSrc.PageNavigator import SelecElement


class MajesticElements:
    CitationFlowSign = 1
    TrustFlowSign = 2
    CitationFlowNumber = 3
    TrustFlowNumber = 4

    @staticmethod
    def get_element_id(element: int)->SelecElement:
            return {
                MajesticElements.CitationFlowSign: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_ddl_majestic_citation'), #option
                MajesticElements.TrustFlowSign: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_ddl_majestic_trust'), #option
                MajesticElements.CitationFlowNumber: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_txt_majestic_citation'), #input
                MajesticElements.TrustFlowNumber: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_txt_majestic_trust'), #input
            }.get(element, None)