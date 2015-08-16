from DomainFinderSrc.PageNavigator import SelecElement


class RegTLD:

    """
    Top Level Domains in RegisterCompass.com
    """
    tld_com = 1
    tld_net = 2
    tld_org = 3
    tld_info = 4
    tld_ca = 5
    tld_us = 6
    tld_eu = 7
    tld_biz = 8
    tld_tv = 9
    tld_me = 10
    tld_de = 11
    tld_cc = 12
    tld_name = 13
    tld_ws = 14
    tld_mobi = 15
    tld_fm = 16
    tld_am = 17
    tld_es = 18
    tld_asia = 19
    tld_se = 20
    tld_xxx = 21
    tld_it = 22
    tld_co_uk = 23
    tld_cn = 24

    def get_tld_id(tld_type: int) ->SelecElement:
        return {
            RegTLD.tld_com: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_chk_tld_com'), # input, checkbox
            RegTLD.tld_net: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_chk_tld_net'),
            RegTLD.tld_org: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_chk_tld_org'),
            RegTLD.tld_info: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_chk_tld_info'),
            RegTLD.tld_ca: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_chk_tld_ca'),
            RegTLD.tld_us: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_chk_tld_us'),
            RegTLD.tld_eu: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_chk_tld_eu'),
            RegTLD.tld_biz: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_chk_tld_biz'),
            RegTLD.tld_tv: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_chk_tld_tv'),
            RegTLD.tld_me: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_chk_tld_me'),
            RegTLD.tld_de: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_chk_tld_de'),
            RegTLD.tld_cc: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_chk_tld_cc'),
            RegTLD.tld_name: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_chk_tld_name'),
            RegTLD.tld_ws: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_chk_tld_ws'),
            RegTLD.tld_mobi: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_chk_tld_mobi'),
            RegTLD.tld_fm: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_chk_tld_fm'),
            RegTLD.tld_am: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_chk_tld_am'),
            RegTLD.tld_es: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_chk_tld_es'),
            RegTLD.tld_asia: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_chk_tld_asia'),
            RegTLD.tld_se: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_chk_tld_se'),
            RegTLD.tld_xxx: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_chk_tld_xxx'),
            RegTLD.tld_it: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_chk_tld_it'),
            RegTLD.tld_co_uk: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_chk_tld_uk'),
            RegTLD.tld_cn: SelecElement('ctl00_IdMemberMainContent_IdUcSearch_chk_tld_cn'),

        }.get(tld_type, None)
