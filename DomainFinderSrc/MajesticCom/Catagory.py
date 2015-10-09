class MainCategory:
    ART = "Arts"
    SOCIETY = "Society"
    BUSINESS = "Business"
    COMPUTER = "Computers"
    INTERNET_SUB_COMPUTER = "Internet Sub Computer"
    SOFTWARE_SUB_COMPUTER = "Software Sub Computer"
    PROGRAMMING_SUB_COMPUTER = "Programming Sub Computer"
    SPORT = "Sports"
    REFERENCES = "References"
    RECREATION = "Recreation"
    NEWS = "News"
    SCIENCE = "Science"
    SHOPPING = "Shopping"
    HEALTH = "Health"
    REGIONAL = "Regional"
    GAMES = "Games"
    VIDEO_GAME_SUB_GAMES = "Video Games Sub Games"
    HOME = "Home"
    ADULT = "Adult"

    @staticmethod
    def get_all_category()->[]:
        return [MainCategory.ART, MainCategory.SOCIETY, MainCategory.BUSINESS, MainCategory.COMPUTER,
                MainCategory.INTERNET_SUB_COMPUTER, MainCategory.SOFTWARE_SUB_COMPUTER,
                MainCategory.PROGRAMMING_SUB_COMPUTER, MainCategory.SPORT, MainCategory.REFERENCES,
                MainCategory.RECREATION, MainCategory.NEWS, MainCategory.SCIENCE, MainCategory.SHOPPING,
                MainCategory.HEALTH, MainCategory.REGIONAL, MainCategory.GAMES, MainCategory.VIDEO_GAME_SUB_GAMES,
                MainCategory.HOME, MainCategory.ADULT, ]


class SubCategory:
    UNDEFINED = "Others"

    def __init__(self, main_category: str, name: str):
        self.main_category = main_category
        self.name = name

    def __str__(self):
        return self.main_category + "/" + self.name

    def __eq__(self, other):
        a = str(self).lower()
        b = str(other).lower()
        if a == b:
            return True
        else:
            return False


class CategoryManager:
    Arts = ["Music", "Television", "Movies", "Performing Arts", "Radio", "People",
            "literature", "Design", "Comics", "Animation", "Visual Arts", "Entertainment", "Writers Resources",
            "Architecture", "Illustration", "Graphic Design", "Online Writing", "Genres", "Art History", "Crafts",
            "Digital", SubCategory.UNDEFINED, ]
    Society = ["Government", "Politics", "People", "Issues", "Religion and Spirituality", "Philanthropy",
               "Law", "Organizations", "Gay Lesbian and Bisexual", "MIlitary", "History", "Ethnicity", "Activism",
               "Work", "Subcultures", "Disabled", "Relationships", "Holidays", "Sexuality", "Folklore", "Paranormal",
               SubCategory.UNDEFINED, ]
    Business = ["Arts and Entertainment", "Financial Services", "Marketing and Advertising",
                "Transportation and Logistics", "Consumer Goods and Services", "Hospitality", "Telecommunications",
                "Business Services", "Food and Related Products", "Pulishing and Printing", "Automotive",
                "Contstruction and Maintenance", "Investing", "Management", "Real Estate", "Small Business",
                "Electronics and Electrical", "Energy", "Employment",
                "Healthcare", "Opportunities", "Industrial Goods and Sevices", "Retail Trade", "Aerospace and Defense",
                "Information Technology", "Biotechnology and pharmaceuticals", "News and Media", "Chemicals",
                "Textiles and Nonwovens", "Hunam Resources", "Major Companies", "Customer Service", "Others", ]
    Computers = ["Internet", "Software", "Programming", "Systems", "Hardware", "Multimedia", "Data Formats",
                 "Open Source", "News and Media", "Security", "Companies", "Data Communications",
                 "Human-Computer Interaction", "Shopping", "Computer Science", "Virtual Reality",
                 "Robotics", "Other", "Education", SubCategory.UNDEFINED, ]
    Internet_Sub_Computer = ["On the Web", "Webdesign and Development", "Searching", "News and Media",
                             "E-mail", "Domain Names", "Resources", "Cloud Computing", "Access providers", "Protocols",
                             "History", "Child Safety", SubCategory.UNDEFINED, ]
    Software_Sub_Computer = ["Internet", "Operating Systems", "Business", "Databases", "Graphics", "Networking",
                             "Accounting", "Desktop Customization", "Editors", "Help Desk", "Industry-specific",
                             "Rentable", "Intranet", SubCategory.UNDEFINED, ]
    Programming_Sub_Computer = ["Languages", "Component Frameworks", "Methodologies", "Resources", "Contests",
                                "Internet", SubCategory.UNDEFINED, ]
    Sports = ["Soccer", "Basketball", "Football", "Motorsports", "Tennis", "Hockey", "Cycling", "Baseball", "Golf",
              "Wrestling", "Cricket", "Equestrian", "Track and Field", "Martial Arts", "Winter Sports", "Running",
              "Water Sports", "Resources", "Multi-Sports", "Volleyball", "People", "Cheerleading",
              "Table Tennis", "Software", SubCategory.UNDEFINED, ]
    References = ["Education", "Museums", "Libraries", "Knowledge Management", "Maps", "Time",
                  "Archives", "Encyclopedias", "Dictionaries", "Ask An Expert", "Bibliography", SubCategory.UNDEFINED, ]
    Recreation = ["Travel", "Food", "Autos", "Radio", "Humor", "Outdoors", "Collecting", "Theme Parks", "Pets",
                  "Boating", "Roads And Highways", "Camps", "Climbing", "Audio", SubCategory.UNDEFINED, ]
    News = ["Newspapers", "Media Industry", "Journalism", "Magazines and E-zines", "Weblogs", "Breaking News",
            "Current Events", "Weather", "Headline Links", "Colleges and Universities", "Extended Coverage", SubCategory.UNDEFINED, ]
    Science = ["Social Sciences", "Technology", "Environment", "Biology", "Earth Sciences", "News and Media",
               "Astronomy", "Physics", "Math", "Events", "Science In Society", "Employment",
               "Instruments and Supplies", SubCategory.UNDEFINED, ]
    Shopping = ["Clothing", "Sports", "Food", "Publications", "Health", "Entertainment", "Jewelry", "Home and Garden",
                "Toys and Games", "Recreation", "Crafts", "Flowers", "Directories", SubCategory.UNDEFINED, ]
    Health = ["Conditions and Diseases", "Medicine", "Mental Health", "Fitness", "Beauty",
              "Organizations", "Nutrition", "Reproductive Health", "Education", "Specific Substance", "Education",
              SubCategory.UNDEFINED, ]
    Regional = ["Europe", "North America", "Asia", "Middle East", "Oceania", SubCategory.UNDEFINED, ]
    Games = ["Video Games", "Gambling", "Board Games", "Role Playing", "Game Studies", "Tile Games", SubCategory.UNDEFINED, ]
    Video_Games_Sub_Games = ["Developers and Publishers", "Roleplaying", "Shooter", "News and Reviews",
                             "Console Platforms", "Sports", "Fighting", "Computer Platforms", "Chats and Forums",
                             "Action-Adventure", "Clans and Guilds", "Strategy", "Action", "Adventure", "Multiplayer",
                             SubCategory.UNDEFINED, ]
    Home = ["Consumer Information", "Cooking", "Personal Finance", "Gardening", "Family", "News and Media",
            "Homeowners", "Homemaking", "Urbanliving", SubCategory.UNDEFINED, ]
    Adult = ["World", "Business", "Recreation", SubCategory.UNDEFINED, ]

    @staticmethod
    def make_sub_categories(main_category: str, sub_category_list: []) ->[]:
        result_list = []
        for item in sub_category_list:
            result_list.append(SubCategory(main_category, item))
        return result_list

    @staticmethod
    def get_sub_categories(main_category: str) -> []:
        return {MainCategory.ART: CategoryManager.Arts,
                MainCategory.SOCIETY: CategoryManager.Society,
                MainCategory.BUSINESS: CategoryManager.Business,
                MainCategory.COMPUTER: CategoryManager.Computers,
                MainCategory.INTERNET_SUB_COMPUTER: CategoryManager.Internet_Sub_Computer,
                MainCategory.SOFTWARE_SUB_COMPUTER: CategoryManager.Software_Sub_Computer,
                MainCategory.PROGRAMMING_SUB_COMPUTER: CategoryManager.Programming_Sub_Computer,
                MainCategory.SPORT: CategoryManager.Sports,
                MainCategory.REFERENCES: CategoryManager.References,
                MainCategory.RECREATION: CategoryManager.Recreation,
                MainCategory.NEWS: CategoryManager.News,
                MainCategory.SCIENCE: CategoryManager.Science,
                MainCategory.SHOPPING: CategoryManager.Shopping,
                MainCategory.HEALTH: CategoryManager.Health,
                MainCategory.REGIONAL: CategoryManager.Regional,
                MainCategory.GAMES: CategoryManager.Games,
                MainCategory.VIDEO_GAME_SUB_GAMES: CategoryManager.Video_Games_Sub_Games,
                MainCategory.HOME: CategoryManager.Home,
                MainCategory.ADULT: CategoryManager.Adult, }.get(main_category, [])

    @staticmethod
    def decode_sub_category(category: str) -> SubCategory:
        if len(category) == 0:
            return None
        main_cat, sub_cat = category.split("/")
        if main_cat not in MainCategory.get_all_category():
            raise ValueError("has to be in main category:" + main_cat)
        sub_cat = sub_cat if len(sub_cat) > 0 else SubCategory.UNDEFINED
        if sub_cat not in CategoryManager.get_sub_categories(main_cat):
            raise ValueError("has to be in sub category:" + sub_cat + " with main category:" + main_cat)
        return SubCategory(main_cat, sub_cat)

    @staticmethod
    def encode_sub_category(category: SubCategory) -> str:
        return str(category)







