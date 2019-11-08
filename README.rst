##################
pfurl - v2.2.2.2
##################

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

``pfurl`` is part of the ``pf`` family of utilities, and used as components of the ChRIS Research Integration System.

In the simplest sense, ``pfurl`` is a wrapper about ``pycurl``, used to send http-based messages to remote services (typically ``pman`` and ``pfioh``). In addition to curl-type http communication, ``pfurl`` also provides some basic file-system services: the ability to zip directories and transmit this to a remote service.

Various authentication options for verifying identify with the remote service are also available.

************
Installation
************

Installation is relatively straightforward, and we recommend using either python virtual environments or docker.

Python Virtual Environment
==========================

On Ubuntu, install the Python virtual environment creator

.. code-block:: bash

  sudo apt install virtualenv virtualenvwrapper python3-tk

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
    mkvirtualenv --python=python3 chris_env

To activate or "enter" the virtual env:

.. code-block:: bash

    workon python_env

To deactivate virtual env:

.. code-block:: bash

    deactivate

Using the ``fnndsc/pfurl`` container
====================================

The easiest option however, is to just use the ``fnndsc/pfurl`` container image.

.. code-block:: bash

    docker pull fnndsc/pfurl
    
and then run

.. code-block:: bash

    docker run --rm --name pfurl fnndsc/pfurl   \
               --VERB POST --raw                \
               --http localhost:5055/api/v1/cmd \
               --httpResponseBodyParse --msg '
               {
                    "someJSONmessage": "Whatever"
               }
               '

where the ``msg`` contains JSON syntax instructions of what to perform.

*****
Usage
*****

For the most up-to-date usage of ``pfurl``, consult the `pfurl wiki page <https://github.com/FNNDSC/pman/wiki/purl-overview>`_.

.. code-block:: html

    ARGS

        [--verb <RESTVERB>]
        The REST verb to use for the remote service.

        [--http <IP>:<port>]                            
        The address of the remote service.

        [--httpProxy [<proto>://]<IP>[:<port>]]
        If specified, instruct ``pfurl`` to use the proxy as specified.
        Currently, only 'http' is supported. Valid values for this flag
        include, for example:

            --httProxy http://proxy.host.org:1234

            --httpProxy proxy.host.org:1234

        [--jsonwrapper <outerMsgJSONwrapper>]
        An optional outer wrapper for the JSON payload.

        [--quiet]                                       
        If specified, only echo the final JSON payload returned
        from remote server.

        [--raw]
        If specified, do not wrap return data from remote call in a 
        JSON wrapper.

        [--oneShot]
        If specified, transmit a shutdown control sequence to remote server
        after communicating. This of course only works for services that
        understand the shutdown protocol.

        [--man <help>]
        Provide detailed help on various topics.

        [-x|--desc]                                     
        Provide an overview help page.

        [-y|--synopsis]
        Provide a synopsis help summary.

        [--content-type <type>]                         
        Curl content-type descriptor.
     
        [--jsonpprintindent <indent>]                   
        If specified, print return JSON payload from remote service using
        <indent> indentation.

        [--httpResponseBodyParse]                       
        If specified, interpret the return payload as encapsulated in an
        http response.

        [--unverifiedCerts]                             
        If specified, allows transmission of https requests with self signed SSL
        certificates.

        [--authToken <token>]
        A token to transmit with an http request. Note, you if you set an 
        --authToken, then you should NOT also set an --auth.

        [--auth <user>:<passwd>]
        A user name and password authentication string.

        [--version]
        Print internal version number and exit.

        [-v|--verbosity <level>]
        Set the verbosity level. "0" typically means no/minimal output. Allows for
        more fine tuned output control as opposed to '--quiet' that effectively
        silences everything.

        --msg <JSONpayload>
        The actual JSON formatted payload to transmit to remote service.

********
Examples
********

Say 'hello' to a ``pfcon`` service listening on the localhost at port 5005:

.. code-block:: bash

            pfurl                                                   \\
                --verb POST --raw                                   \\
                --http 127.0.0.1:5005/api/v1/cmd                     \\
                --jsonwrapper 'payload'                             \\
                --msg                                               \\
                    '{  "action": "hello",
                            "meta": {
                                    "askAbout":     "sysinfo",
                                    "echoBack":     "Hi there!"
                            }
                    }' --quiet --jsonpprintindent 4 

and print response "prettily" using an indent of 4.



