# -*- coding: UTF-8 -*-

from setuptools import setup, find_packages

'''
How to build and upload this package to PyPi
    python setup.py sdist
    python setup.py bdist_wheel --universal
    twine upload dist/*
'''

setup (
    name='robotframework-comparelibrary',
    version='0.0.1',
    description='Robot Framework keyword library for textual diffing',
    keywords     = 'robotframework testing test automation diff textual',
    platforms    = 'any',
    install_requires=['robotframework',],

    author='RobotSlacker',
    author_email='184902652@qq.com',
    url='https://github.com/robotslacker/robotframework-comparelibrary',

    packages     = ['CompareLibrary'],
    package_data = {'CompareLibrary': ['tests/*.txt']}
)   
