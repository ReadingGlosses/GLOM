from setuptools import setup

APP = ['glom.py']
OPTIONS = {
    'argv_emulation': True,
    'packages': ['fpdf'],
}

setup(
    app=APP,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)