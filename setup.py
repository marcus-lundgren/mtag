#!/usr/bin/env python

import setuptools
from setuptools import setup

setup(
        name='mtag',
        version='0.1.0',
        packages=['mtag', "mtag.entity", "mtag.widget", "mtag.repository", "mtag.helper"],
        url='',
        license='',
        author='ML',
        author_email='',
        description='',
        python_requires='>=3.8',
        scripts=["start_mtag"]
)
