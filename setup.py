# -*- coding: UTF-8 -*-
import ast
from io import open
import re
from setuptools import setup

'''
How to build and upload this package to PyPi
    python setup.py sdist
    python setup.py bdist_wheel --universal
    twine upload dist/*
'''
_version_re = re.compile(r"ROBOT_LIBRARY_VERSION\s+=\s+(.*)")

with open("CompareLibrary/__init__.py", "rb") as f:
    version = str(
        ast.literal_eval(_version_re.search(f.read().decode("utf-8")).group(1))
    )

setup(
    name='robotframework-comparelibrary',
    version=version,
    description='Robot Framework keyword library for textual diffing',
    keywords='robotframework testing test automation diff textual',
    platforms='any',
    install_requires=['robotframework', ],

    author='RobotSlacker',
    author_email='184902652@qq.com',
    url='https://github.com/robotslacker/robotframework-comparelibrary',

    zip_safe=False,
    packages=['CompareLibrary'],
    package_data={'CompareLibrary': []}
)   
