import os
from setuptools import setup


# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='timeflow',
    packages=['timeflow'],
    version='0.1.3',
    description='Small CLI time logger',

    author='Justas Trimailovas',
    author_email='j.trimailvoas@gmail.com',

    url='https://github.com/trimailov/timeflow',
    keywords=['timelogger', 'logging', 'timetracker', 'tracker'],

    long_description=read('README.rst'),

    install_requires=[
        'termcolor'
    ],
    test_suite='tests.tests',

    entry_points='''
        [console_scripts]
        timeflow=timeflow.main:main
        tf=timeflow.main:main
        tl=timeflow.main:log
        ts=timeflow.main:stats_report
        te=timeflow.main:edit
    ''',
)
