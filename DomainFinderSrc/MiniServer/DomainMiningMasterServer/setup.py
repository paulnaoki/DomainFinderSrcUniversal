from distutils.core import setup

setup(
    # Application name:
    name="MiningSlaveServer",

    # Version number (initial):
    version="1.0.0",

    # Application author details:
    author="li zhang",
    author_email="li.zhang@iristronics.com",

    # Packages
    packages=["MiningServer"],

    # Include additional files into the package
    include_package_data=False,

    # Details
    #url="http://pypi.python.org/pypi/MyApplication_v010/",

    #
    # license="LICENSE.txt",
    description="a master server to control mining slave servers, and communicate with user interface(webserver)",

    # long_description=open("README.txt").read(),

    # Dependent packages (distributions)
    install_requires=[

    ],
)
