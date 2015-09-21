from distutils.core import setup

setup(
    name='DomainFinderSrc',
    version='1.0.4.1',
    packages=['DomainFinderSrc', 'DomainFinderSrc.xlrd', 'DomainFinderSrc.MozCom',
              'DomainFinderSrc.Scrapers', 'DomainFinderSrc.Scrapers.SiteTempDataSrc',
              'DomainFinderSrc.ArchiveOrg',
              'DomainFinderSrc.GoogleCom', 'DomainFinderSrc.SiteConst',
              'DomainFinderSrc.GoDaddyCom', 'DomainFinderSrc.GoDaddyCom.Elements',
              'DomainFinderSrc.GoDaddyCom.Elements.Selectors', 'DomainFinderSrc.MiniServer',
              'DomainFinderSrc.MiniServer.Common', 'DomainFinderSrc.MiniServer.DomainMiningSlaveServer',
              'DomainFinderSrc.MiniServer.DomainMiningMasterServer', 'DomainFinderSrc.MajesticCom',
              'DomainFinderSrc.RegisterCompassCom', 'DomainFinderSrc.RegisterCompassCom.Elements',
              'DomainFinderSrc.RegisterCompassCom.Selectors', 'DomainFinderSrc.UserAccountSettings',
              'DomainFinderSrc.Utilities',
              'DomainFinderSrc.BingCom',
              'pythonwhois'],

    #package_dir={"pythonwhois": "pythonwhois"},
    package_data={"pythonwhois": ["*.dat"]},
    url='',
    license='',
    author='Li Zhang',
    author_email='',
    description='source file for scraper',

    install_requires=[
        'argparse',
        "pytz",  # new package since 1.0.0.7
        "requests",
        "beautifulsoup4",
        "tldextract",
        "selenium",
        "tornado",
        "psutil",
        'shortuuid',
        ],
        # Dependent packages (distributions)
    # requires=[
    #     "pytz",
    #     "requests",
    #     "beautifulsoup4",
    #     "tldextract",
    #     "selenium",
    #     "tornado",
    #     "psutil",
    # ],
)
