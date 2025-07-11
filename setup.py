from setuptools import setup

# read the long description from README.rst
long_description = open("README.rst", encoding="utf-8").read()

setup(
    name="pibooth-date-folder",
    version="1.3.0",                    # bump this on each release
    description="PiBooth plugin to split output folders by date+threshold",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    author="Kenneth Nicholas Jørgensen",
    author_email="you@example.com",
    url="https://github.com/DJ-Dingo/pibooth-date-folder",
    py_modules=["pibooth_date_folder"],  # your single .py file
    install_requires=[
        "pibooth>=2.8.0",
    ],
    entry_points={
        "pibooth.plugins": [
            # load your module as a PiBooth plugin
            "date_folder = pibooth_date_folder",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Framework :: PiBooth",
        "License :: OSI Approved :: MIT License",
    ],
)
