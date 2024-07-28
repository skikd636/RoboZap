from setuptools import setup
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='RoboZap',
    version='1.4.0',
    packages=[''
              ''
              ''],
    package_dir={'': 'robozap'},
    url='https://www.github.com/we45/RoboZap',
    license='MIT',
    author='we45',
    author_email='info@we45.com',
    description='Robot Framework Library for the OWASP ZAP Application Vulnerability Scanner' ,
    install_requires=[
        'requests>=2.32.3',
        'zaproxy>=0.3.2',
        'robotframework>=6.1'
    ],
    long_description = long_description,
    long_description_content_type='text/markdown'
)
