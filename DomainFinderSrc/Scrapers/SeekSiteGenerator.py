class SeedSiteSettings:
    TIME_LAST_YEAR = "LAST_YEAR"
    TIME_LAST_MONTH = "LAST_MONTH"
    TIME_LAST_WEEK = "LAST_WEEK"
    TIME_LAST_DAY = "LAST_DAY"
    TIME_NOW = "NOW"


class SeedSiteGeneratorInterface:
    @staticmethod
    def get_sites(keyword: str, page: int=1, index: int=0, length: int=100,
                  history=SeedSiteSettings.TIME_NOW, blog=False) -> []:
        pass

    @staticmethod
    def get_result_per_page_range()-> []:
        """
        get maximum number of results per search query in a range of numbers. e.g: [10,20,50,100]
        :return: a list of available numbers
        """
        pass

    @staticmethod
    def get_suggestion(keywords: [], proxies: [], interval=2) -> []:
        pass