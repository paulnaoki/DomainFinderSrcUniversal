import re
from DomainFinderSrc.Utilities.Serializable import Serializable

default_catalgory_pattern = re.compile(u'([a-zA-Z\s]+)\/(.*)')


class MainCategory:
    ART = "Arts"
    SOCIETY = "Society"
    BUSINESS = "Business"
    COMPUTER = "Computers"
    # INTERNET_SUB_COMPUTER = "Internet Sub Computer"
    # SOFTWARE_SUB_COMPUTER = "Software Sub Computer"
    # PROGRAMMING_SUB_COMPUTER = "Programming Sub Computer"
    SPORT = "Sports"
    REFERENCES = "Reference"
    RECREATION = "Recreation"
    NEWS = "News"
    SCIENCE = "Science"
    SHOPPING = "Shopping"
    HEALTH = "Health"
    REGIONAL = "Regional"
    GAMES = "Games"
    # VIDEO_GAME_SUB_GAMES = "Video Games Sub Games"
    HOME = "Home"
    ADULT = "Adult"
    UNDEFINED = "General"

    @staticmethod
    def get_all_category()->[]:
        return [MainCategory.ART, MainCategory.SOCIETY, MainCategory.BUSINESS, MainCategory.COMPUTER,
                # MainCategory.INTERNET_SUB_COMPUTER, MainCategory.SOFTWARE_SUB_COMPUTER,
                # MainCategory.PROGRAMMING_SUB_COMPUTER,
                MainCategory.SPORT, MainCategory.REFERENCES,
                MainCategory.RECREATION, MainCategory.NEWS, MainCategory.SCIENCE, MainCategory.SHOPPING,
                MainCategory.HEALTH, MainCategory.REGIONAL, MainCategory.GAMES,
                # MainCategory.VIDEO_GAME_SUB_GAMES,
                MainCategory.HOME, MainCategory.ADULT, ]


class SubCategory(Serializable):
    UNDEFINED = "General"

    def __init__(self, main_category: str="", name: str=""):
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
    Arts = ["Music", "Television", "Movies", "Performing Arts", "Radio", "People", "Photography", "Literature",
            "literature", "Design", "Comics", "Animation", "Visual Arts", "Entertainment", "Writers Resources",
            "Architecture", "Illustration", "Graphic Design", "Online Writing", "Genres", "Art History", "Crafts",
            "Digital", "Directories", "Organizations", "Bodyart", "Education", "Magazines and E-zines", "Humanities",
            "Other", "Costumes", "Weblogs", SubCategory.UNDEFINED, ]
    Society = ["Government", "Politics", "People", "Issues", "Religion and Spirituality", "Philanthropy",
               "Law", "Organizations", "Gay  Lesbian  and Bisexual", "History", "Ethnicity", "Activism",
               "Work", "Subcultures", "Disabled", "Relationships", "Holidays", "Sexuality", "Folklore", "Paranormal",
               "Philosophy", "Military", "Genealogy", "Death", "Support Groups", "Transgendered", "Lifestyle Choices",
               "Future", "Crime", SubCategory.UNDEFINED, ]
    Business = ["Arts and Entertainment", "Agriculture and Forestry", "Financial Services", "Marketing and Advertising",
                "Transportation and Logistics", "Consumer Goods and Services", "Hospitality", "Telecommunications",
                "Business Services", "Food and Related Products", "Publishing and Printing", "Automotive",
                "Construction and Maintenance", "Investing", "Management", "Real Estate", "Small Business",
                "Electronics and Electrical", "Energy", "Employment", "Directories", "Materials", "Environment",
                "Healthcare", "Opportunities", "Industrial Goods and Services", "Retail Trade", "Aerospace and Defense",
                "Information Technology", "Biotechnology and pharmaceuticals", "News and Media", "Chemicals", "Information Services",
                "Textiles and Nonwovens", "Human Resources", "Major Companies", "Industrial Goods and Services",
                "E-Commerce", "Education and Training", "Accounting", "Resources", "Associations", "Mining and Drilling",
                "Customer Service", "Others", "Cooperatives", "Biotechnology and Pharmaceuticals",
                "International Business and Trade", SubCategory.UNDEFINED, ]
    Computers = ["Internet", "History", "Software", "Graphics", "Programming", "Systems", "Hardware", "Multimedia",
                 "Data Formats", "Consultants", "Artificial Intelligence", "Parallel Computing", "Organizations",
                 "Open Source", "News and Media", "Security", "Companies", "Data Communications", "FAQs  Help  and Tutorials",
                 "Human-Computer Interaction", "Shopping", "Computer Science", "Virtual Reality", "Artificial Life",
                 "Robotics", "Other", "Education", "Hacking", "Ethics", "Chats and Forums", "Speech Technology",
                 "Usenet", "E-Books", "Desktop Publishing",  "Mobile Computing", "Supercomputing", "Performance and Capacity",
                 "Emulators", "CAD and CAM", SubCategory.UNDEFINED, ]
    Science_Sub_Computer = ["Academic Departments",  SubCategory.UNDEFINED, ]
    for item in Science_Sub_Computer:
        Computers.append("Science/"+item)
    Internet_Sub_Computer = ["On the Web", "Web Design and Development", "Searching", "News and Media",
                             "E-mail", "Domain Names", "Resources", "Cloud Computing", "Access providers", "Protocols",
                             "History", "Child Safety", "Cybercafes", "Chat", "Education", "FAQs  Help  and Tutorials",
                             "Proxying and Filtering", "Access Providers", "Publications", "Broadcasting",
                             "Internet Fax", "Commercial Services", "Routers and Routing", "WWW", "File Sharing",
                             "Abuse", "Organizations", "Etiquette", "Telephony", SubCategory.UNDEFINED, ]
    for item in Internet_Sub_Computer:
        Computers.append("Internet/"+item)
    Software_Sub_Computer = ["Internet", "Operating Systems", "Business", "Databases", "Graphics", "Networking",
                             "Accounting", "Desktop Customization", "Editors", "Help Desk", "Industry-Specific",
                             "Rentable", "Intranet", "Disk Management", "Shareware", "Manufacturing", "Educational",
                             "Information Retrieval", "File Management", "Globalization", "Freeware", "Directories",
                             "Retailers", "Online Training", "Document Management", "Consultants", "Project Management",
                             "ERP", "Data Compression", "Groupware", "Backup", "Office Suites", "Configuration Management",
                             "Data Administration", "Spreadsheets", "System Management", "Typesetting",
                             "Software Engineering", SubCategory.UNDEFINED, ]
    for item in Software_Sub_Computer:
        Computers.append("Software/"+item)
    Programming_Sub_Computer = ["Languages", "Component Frameworks", "Methodologies", "Resources", "Contests", "Education",
                                "Internet",  "Software Testing", "Personal Pages", "Games", "Compilers", "Operating Systems",
                                "Graphics", "FAQs  Help  and Tutorials",  "Agents", SubCategory.UNDEFINED, ]
    for item in Programming_Sub_Computer:
        Computers.append("Programming/"+item)
    Computer_Science_Sub_Computer = ["People", "Academic Departments", "Publications",  "Distributed Computing",
                                     "Organizations", "Conferences", "Computer Graphics", SubCategory.UNDEFINED, ]
    for item in Computer_Science_Sub_Computer:
        Computers.append("Computer Science/"+item)
    Sports = ["Soccer", "Basketball", "Football", "Motorsports", "Tennis", "Hockey", "Cycling", "Baseball", "Golf",
              "Wrestling", "Cricket", "Equestrian", "Track and Field", "Martial Arts", "Winter Sports", "Running", "Walking",
              "Water Sports", "Resources", "Multi-Sports", "Volleyball", "People", "Cheerleading", "Events", "Croquet",
              "Table Tennis", "Software", "Skating", "Strength Sports", "Skateboarding", "Fantasy", "Bowling", "Cue Sports",
              "College and University", "Informal Sports", "Flying Discs", "Boxing", "Squash", "Paintball", "Airsoft",
              "Darts", "Team Handball", "Organizations", "Orienteering", "Archery", "Softball", "Disabled", "Laser Games",
              "Adventure Racing", "Petanque", "Animal Sports", "Extreme Sports", "Goalball", "Lacrosse", SubCategory.UNDEFINED, ]
    References = ["Education", "Museums", "Libraries", "Knowledge Management", "Maps", "Time", "Parliamentary Procedure", "World Records",
                  "Archives", "Encyclopedias", "Dictionaries", "Ask an Expert", "Bibliography", "Directories",
                  "Quotations", "Almanacs", "Journals", "Flags", "Thesauri", SubCategory.UNDEFINED, ]
    Recreation = ["Aviation", "Travel", "Food", "Autos", "Motorcycles", "Radio", "Humor", "Outdoors", "Collecting",
                  "Theme Parks", "Pets", "Models", "Drugs", "Birding", "Antiques", "Parties", "Guns", "Scouting",
                  "Boating", "Roads and Highways", "Camps", "Climbing", "Audio", "Living History",
                  "Trains and Railroads", "Nudism", "Tobacco", "Picture Ratings", "Knives", "Kites",
                  SubCategory.UNDEFINED, ]
    News = ["Newspapers", "Analysis and Opinion", "Media Industry", "Journalism", "Magazines and E-zines", "Weblogs",
            "Breaking News", "Alternative", "Directories",
            "Current Events", "Weather", "Headline Links", "Colleges and Universities", "Extended Coverage",
            SubCategory.UNDEFINED, ]
    Science = ["Social Sciences", "Technology", "Environment", "Biology", "Chemistry", "Earth Sciences", "News and Media",
               "Astronomy", "Physics", "Math", "Events", "Science In Society", "Employment", "Science in Society",
               "Instruments and Supplies", "Anomalies and Alternative Science", "Agriculture", "Organizations", "Publications",
               "Educational Resources", "Methods and Techniques", "Research Groups and Centers",
               "Directories", SubCategory.UNDEFINED, ]
    Shopping = ["Clothing", "Niche", "Sports", "Food", "Publications", "Health", "Entertainment", "Jewelry", "Home and Garden",
                "Classifieds", "Pets", "Ethnic and Regional", "Consumer Electronics", "Music", "Antiques and Collectibles",
                "Toys and Games", "Recreation", "Crafts", "Flowers", "Directories", "Children", "Weddings", "Vehicles",
                "Visual Arts", "Gifts", "Travel", "Photography", "Office Products", "Holidays", "Tobacco", "Death Care",
                "Tools", "Auctions", "General Merchandise", SubCategory.UNDEFINED, ]
    Health = ["Conditions and Diseases", "Medicine", "Mental Health", "Public Health and Safety", "Fitness", "Beauty",
              "Addictions", "Alternative", "Dentistry", "Animal", "Professions", "News and Media", "Search Engines",
              "Organizations", "Nutrition", "Reproductive Health", "Education", "Specific Substance", "Education",
              "Specific Substances", "Men's Health", "Women's Health", "Child Health", "Senior Health", "Nursing", "Resources", "Pharmacy", "Home Health",
              "Occupational Health and Safety", "Services", "Aging", "Senses", SubCategory.UNDEFINED, ]
    Regional = ["Europe", "North America", "Asia", "Middle East", "Oceania", "Africa", "South America", "Caribbean",
                "Polar Regions", "Central America", SubCategory.UNDEFINED, ]
    Games = ["Video Games", "Online", "Gambling", "Board Games", "Role Playing", "Game Studies", "Tile Games", "Music",
             "Trading Card Games", "Miniatures", "Yard  Deck  and Table Games", "Puzzles", "Roleplaying", "Coin-Op",
             "Card Games", "Conventions", "Paper and Pencil", "Party Games", "Play Groups",
             SubCategory.UNDEFINED, ]
    Video_Games_Sub_Games = ["Developers and Publishers", "Roleplaying", "Shooter", "News and Reviews",
                             "Music", "Music and Dance", "Simulation", "Recreation", "Browser Based", "Game Design",
                             "Console Platforms", "Sports", "Fighting", "Computer Platforms", "Chats and Forums",
                             "Action-Adventure", "Clans and Guilds", "Strategy", "Action", "Adventure", "Multiplayer",
                             "Driving and Racing", "Emulation", "Puzzle", "History", "Massive Multiplayer Online",
                             "Cheats and Hints", "Platform", "Downloads", "Fan Pages", "Word Games", SubCategory.UNDEFINED, ]
    for item in Video_Games_Sub_Games:
        Games.append("Video Games/" + item)
    Home = ["Consumer Information", "Cooking", "Personal Finance", "Gardening", "Family", "News and Media",
            "Home Improvement", "Rural Living", "Personal Organization", "Do-It-Yourself",
            "Homeowners", "Homemaking", "Urban Living", "Moving and Relocating", SubCategory.UNDEFINED, ]
    Adult = ["World", "Business", "Recreation", "Regional", "Society", "Image Galleries", "Arts", "Shopping",
             "Niche", "Computers", SubCategory.UNDEFINED, ]

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
                # MainCategory.INTERNET_SUB_COMPUTER: CategoryManager.Internet_Sub_Computer,
                # MainCategory.SOFTWARE_SUB_COMPUTER: CategoryManager.Software_Sub_Computer,
                # MainCategory.PROGRAMMING_SUB_COMPUTER: CategoryManager.Programming_Sub_Computer,
                MainCategory.SPORT: CategoryManager.Sports,
                MainCategory.REFERENCES: CategoryManager.References,
                MainCategory.RECREATION: CategoryManager.Recreation,
                MainCategory.NEWS: CategoryManager.News,
                MainCategory.SCIENCE: CategoryManager.Science,
                MainCategory.SHOPPING: CategoryManager.Shopping,
                MainCategory.HEALTH: CategoryManager.Health,
                MainCategory.REGIONAL: CategoryManager.Regional,
                MainCategory.GAMES: CategoryManager.Games,
                # MainCategory.VIDEO_GAME_SUB_GAMES: CategoryManager.Video_Games_Sub_Games,
                MainCategory.HOME: CategoryManager.Home,
                MainCategory.ADULT: CategoryManager.Adult, }.get(main_category, [])

    @staticmethod
    def decode_sub_category(category: str, strict_check=True) -> SubCategory:
        if len(category) == 0:
            return SubCategory(MainCategory.UNDEFINED, MainCategory.UNDEFINED)
        if "/" not in category:
            main_cat = category
            sub_cat = ""
        else:
            match = re.search(default_catalgory_pattern, category)
            if match is not None:
                groups = match.groups()
                if isinstance(groups, tuple) and len(groups) == 2:
                    main_cat, sub_cat = groups
                else:
                    raise ValueError("parsing category error:" + category)
            else:
                raise ValueError("parsing category error:" + category)
        if main_cat not in MainCategory.get_all_category():
            raise ValueError("has to be in main category:" + category)
        sub_cat = sub_cat if len(sub_cat) > 0 else SubCategory.UNDEFINED
        if strict_check and sub_cat not in CategoryManager.get_sub_categories(main_cat):
            raise ValueError("has to be in sub category:" + sub_cat + " with main category:" + main_cat)
        return SubCategory(main_cat, sub_cat)

    @staticmethod
    def encode_sub_category(category: SubCategory) -> str:
        return str(category)







