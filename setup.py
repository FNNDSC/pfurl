import sys
# Make sure we are running python3.5+
if 10 * sys.version_info[0]  + sys.version_info[1] < 35:
    sys.exit("Sorry, only Python 3.5+ is supported.")

from setuptools import setup


def readme():
    with open('README.rst') as f:
        return f.read()

setup(
      name             =   'pfurl',
      version          =   '1.0.2',
      description      =   '(Python) Process Manager',
      long_description =   readme(),
      author           =   'Rudolph Pienaar',
      author_email     =   'rudolph.pienaar@gmail.com',
      url              =   'https://github.com/FNNDSC/pfurl',
      packages         =   ['pfurl'],
      install_requires =   ['pycurl', 'pyzmq', 'webob', 'pudb', 'psutil'],
      test_suite       =   'nose.collector',
      tests_require    =   ['nose'],
      scripts          =   ['bin/pfurl'],
      license          =   'MIT',
      zip_safe         =   False
     )
