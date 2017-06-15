##############
pfurl - v1.2.4
##############

.. image:: https://badge.fury.io/py/pfurl.svg
    :target: https://badge.fury.io/py/pfurl

.. image:: https://travis-ci.org/FNNDSC/pfurl.svg?branch=master
    :target: https://travis-ci.org/FNNDSC/pfurl

.. image:: https://img.shields.io/badge/python-3.5%2B-blue.svg
    :target: https://badge.fury.io/py/pfurl

.. contents:: Table of Contents

********
Overview
********

This repository provides a curl-like client tool that is also able to perform simple file/directory functions (such as zip/unzip) suitable for remote http transmission:

- ``pfurl``: a tool to transfer data using HTTP (similar to ``curl``);

pfurl
=====

A client application called ``pfurl`` is provided that can be used to speak to both ``pman`` and ``pfioh``.

************
Installation
************

Installation is relatively straightforward, and we recommend using either python virtual environments or docker.

Python Virtual Environment
==========================

On Ubuntu, install the Python virtual environment creator

.. code-block:: bash

  sudo apt install virtualenv

Then, create a directory for your virtual environments e.g.:

.. code-block:: bash

  mkdir ~/python-envs

You might want to add to your .bashrc file these two lines:

.. code-block:: bash

    export WORKON_HOME=~/python-envs
    source /usr/local/bin/virtualenvwrapper.sh

Then you can source your .bashrc and create a new Python3 virtual environment:

.. code-block:: bash

    source .bashrc
    mkvirtualenv --python=python3 python_env

To activate or "enter" the virtual env:

.. code-block:: bash

    workon python_env

To deactivate virtual env:

.. code-block:: bash

    deactivate

Using the ``fnndsc/ubuntu-python3`` dock
========================================

We provide a slim docker image with python3 based off Ubuntu. If you want to play inside this dock and install ``pman`` manually, do

.. code-block:: bash

    docker pull fnndsc/ubuntu-python3

This docker has an entry point ``python3``. To enter the dock at a different entry and install your own stuff:

.. code-block:: bash

   docker run -ti --entrypoint /bin/bash fnndsc/ubuntu-python3
   
Now, install ``pman`` and friends using ``pip``

.. code-block:: bash

   apt update && \
   apt install -y libssl-dev libcurl4-openssl-dev librtmp-dev && \
   pip install pfurl
   
**If you do the above, remember to** ``commit`` **your changes to the docker image otherwise they'll be lost when you remove the dock instance!**

.. code-block:: bash

  docker commit <container-ID> local/ubuntu-python3-pman
  
 where ``<container-ID>`` is the ID of the above container.
  

Using the ``fnndsc/pman`` dock
==============================

The easiest option however, is to just use the ``fnndsc/pman`` dock.

.. code-block:: bash

    docker pull fnndsc/pfurl
    
and then run

.. code-block:: bash

    docker run --name pfurl fnndsc/pfurl --VERB POST --raw --http localhost:5055/api/v1/cmd --httpResponseBodyParse --msg '{}'

where the ``msg`` contains JSON syntax instructions of what to perform.

*****
Usage
*****

For usage of ``pfurl``, consult the relevant wiki pages.

``pfurl`` usage
===============

For ``pfurl`` detailed information, see the `pfurl wiki page <https://github.com/FNNDSC/pman/wiki/purl-overview>`_.



