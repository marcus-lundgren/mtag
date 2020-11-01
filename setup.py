#!/usr/bin/env python

import setuptools
from setuptools import setup

setup(
    name='mtag',
    version='0.1.0',
    packages=['mtag',
              "mtag.entity",
              "mtag.widget",
              "mtag.repository",
              "mtag.helper",
              "mtag.watcher"],
    url='https://github.com/marcus-lundgren',
    license='GPLv3',
    author='Marcus Lundgren',
    author_email='marcus.lundgren@gmail.com',
    description='',
    python_requires='>=3.6',
    scripts=["script/mtag", "script/watcher"],
    package_data={"mtag.helper": ["schema.sql"]}
)
