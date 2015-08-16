from DomainFinderSrc.Scrapers.LinkChecker import LinkChecker


class LinkExtension:
    EXT_CSS = 'css'
    EXT_JS = 'js'
    EXT_WEBPAGE = 'html'
    EXT_IMAGE = 'image'
    EXT_OTHER = 'other'

    @staticmethod
    def get_link_class(link: str):
        ext = LinkChecker.get_link_extension(link).lower()
        if len(ext) == 0 or ext in LinkChecker.common_html_page_ex:
            return LinkExtension.EXT_WEBPAGE
        elif ext in LinkChecker.common_img_ex:
            return LinkExtension.EXT_IMAGE
        elif ext == '.css':
            return LinkExtension.EXT_CSS
        elif ext == '.js':
            return LinkExtension.EXT_JS
        else:
            return LinkExtension.EXT_OTHER


