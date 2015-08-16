from DomainFinderSrc.PageNavigator import SelecElement


class DownloadActionElements:
    SearchButton = 1
    ExpiredDomainNumber = 2  # this only occur after SearchButton clicked
    ExpiredDomainExcel = 3   # this only occur after SearchButton clicked
    ResultPageMenu = 4       # this only occur after ExpiredDomainNumber clicked
    DownloadResButton = 5    # this only occur after ExpiredDomainExcel clicked
    DownloadFormatOpt = 6    # this only occur after ExpiredDomainExcel clicked
    FinalDownloadBut = 7     # this only occur after DownloadResButton clicked, #  check for inner anchor link to download final result
    DownloadPageFrame = 8    # this iframe contains DownloadRestButton and DownloadFormatOpt and FinalDownloadBut, change to this context to continue

    @staticmethod
    def get_element_id(id)->SelecElement:
        return {
            DownloadActionElements.SearchButton: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_lb_calculate'),
            DownloadActionElements.ExpiredDomainNumber: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_lbl_result_count_ex'),
            DownloadActionElements.ExpiredDomainExcel: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_img_export_ex'),
            DownloadActionElements.ResultPageMenu: SelecElement('ctl00_IdMemberMainContent_lbl_menu'),
            DownloadActionElements.DownloadResButton: SelecElement('ctl00_IdIFrameMainContent_lb_download'),
            DownloadActionElements.DownloadFormatOpt: SelecElement('ctl00_IdIFrameMainContent_ddl_format'),  # <option> choose the 4th item
            DownloadActionElements.FinalDownloadBut: SelecElement('ctl00_IdIFrameMainContent_lbl_result'),
            DownloadActionElements.DownloadPageFrame: SelecElement('iframe_modal'),
        }.get(id, None)
