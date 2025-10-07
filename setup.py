from pathlib import Path
import re
from setuptools import setup

HERE = Path(__file__).parent
MODULE = HERE / "pibooth_date_folder.py"

# Parse version without importing the module
TEXT = MODULE.read_text(encoding="utf-8")
VERSION = re.search(r'__version__\s*=\s*"([^"]+)"', TEXT).group(1)

setup(
    name="pibooth-date-folder",
    version=VERSION,
    author="Kenneth Nicholas Jørgensen",
    author_email="",
    description="PiBooth plugin to split/save sessions into date-based folders with an optional daily time threshold.",
    long_description=(HERE / "README.rst").read_text(encoding="utf-8"),
    long_description_content_type="text/x-rst",
    url="https://github.com/DJ-Dingo/pibooth-date-folder",
    project_urls={
        "Homepage": "https://github.com/DJ-Dingo/pibooth-date-folder",
        "Repository": "https://github.com/DJ-Dingo/pibooth-date-folder",
        "Issues": "https://github.com/DJ-Dingo/pibooth-date-folder/issues",
    },

    py_modules=["pibooth_date_folder"],

    install_requires=[
        "pibooth>=2.0.8",
    ],
    python_requires=">=3.6",

    entry_points = {
        "pibooth": [
            "date_folder = pibooth_date_folder",
        ],
    },

    license="GPL-3.0-or-later",
    keywords=[
        "pibooth", "pibooth plugin", "plugin",
        "photobooth", "selfiecam",
        "raspberry", "raspberry pi",
        "date", "folder", "sessions", "organize",
        "camera", "kiosk", "Raspberry Pi OS", "python"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)


