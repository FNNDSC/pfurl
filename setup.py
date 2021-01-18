from os import path
from setuptools import setup

with open(path.join(path.abspath(path.dirname(__file__)), 'README.rst')) as f:
    readme = f.read()

setup(
    name             =   'pfurl',
    version          =   '2.3.1',
    description      =   'Path-File URL communication',
    long_description =   readme,
    author           =   'Rudolph Pienaar',
    author_email     =   'rudolph.pienaar@gmail.com',
    url              =   'https://github.com/FNNDSC/pfurl',
    packages         =   ['pfurl'],
    install_requires =   ['pycurl', 'pyzmq', 'webob', 'pudb', 'psutil', 'pfmisc'],
    scripts          =   ['bin/pfurl'],
    license          =   'MIT',
    zip_safe         =   False,
    python_requires  =   '>=3.6'
)
