#!/usr/bin/env python3

'''
        __            _
       / _|          | |
 _ __ | |_ _   _ _ __| |
| '_ \|  _| | | | '__| |
| |_) | | | |_| | |  | |
| .__/|_|  \__,_|_|  |_|
| |
|_|

                            Process-File-over-URL

    'pfurl' sends REST conforming commands and data to remote services,
    similar in some ways to the well-known CLI tool, 'curl' or the Python
    tool, 'httpie'.

    'pfurl' not only sends curl type payloads, but can also zip/unzip
    entire directories of files for transmission and reception.

    'pfurl' is designed to be part of the ChRIS framework but can also be
    used in similar use cases to 'curl' or 'httpie'.


'''


import  sys
import  json
import  pprint
import  pycurl
import  io
import  os
import  urllib.parse
import  datetime
import  zipfile
import  uuid
import  base64
import  yaml
import  shutil
import  inspect
import  glob

from    urllib.parse        import urlparse

# import  codecs

import  pudb
import  pfmisc

# pfurl local dependencies
from    pfmisc._colors      import  Colors
from    pfmisc.message      import  Message

# A global variable that tracks if script was started from CLI or programmatically
Gb_startFromCLI             = False


class Pfurl():

    ''' Represents an example client. '''

    def col2_print(self, str_left, str_right):
        print(Colors.WHITE +
              ('%*s' % (self.LC, str_left)), end='')
        print(Colors.LIGHT_BLUE +
              ('%*s' % (self.RC, str_right)) + Colors.NO_COLOUR)

    def __init__(self, **kwargs):
        # threading.Thread.__init__(self)

        self._log                       = Message()
        self._log._b_syslog             = True
        self.__name__                   = "Pfurl"
        self.b_useDebug                 = False
        self._startFromCLI              = False

        str_debugDir                    = '%s/tmp' % os.environ['HOME']
        if not os.path.exists(str_debugDir):
            os.makedirs(str_debugDir)
        self.str_debugFile              = '%s/debug-pfurl.log' % str_debugDir

        self.verbosity                  = 0

        self.str_http                   = ""
        self.str_ip                     = ""
        self.str_port                   = ""
        self.str_URL                    = ""
        self.str_verb                   = ""
        self.str_msg                    = ""
        self.str_auth                   = ""
        self.d_msg                      = {}
        self.str_protocol               = "http"
        self.pp                         = pprint.PrettyPrinter(indent=4)
        self.b_man                      = False
        self.str_man                    = ''
        self.b_quiet                    = False
        self.b_raw                      = False
        self.b_oneShot                  = False
        self.b_httpResponseBodyParse    = False
        self.auth                       = ''
        self.str_jsonwrapper            = ''
        self.str_contentType            = ''
        self.b_useDebug                 = False
        self.str_debugFile              = ''

        self.LC                         = 40
        self.RC                         = 40
        self.str_name                   = ''
        self.str_version                = ''
        self.str_desc                   = ''
        self.b_unverifiedCerts          = False
        self.str_authToken              = ''

        # Curl stuff
        self.c                          = None
        self.buffer                     = None
        self.HTTPheaders                = []
        self.str_httpProxy              = ''

        for key,val in kwargs.items():
            if key == 'msg':
                self.str_msg                = val
                try:
                    self.d_msg              = json.loads(self.str_msg)
                except:
                    pass
            if key == 'http':                       self.httpStr_parse(http         = val)
            if key == 'auth':                       self.str_auth                   = val
            if key == 'verb':                       self.str_verb                   = val
            if key == 'contentType':                self.str_contentType            = val
            if key == 'ip':                         self.str_ip                     = val
            if key == 'port':                       self.str_port                   = val
            if key == 'b_quiet':                    self.b_quiet                    = val
            if key == 'b_raw':                      self.b_raw                      = val
            if key == 'b_oneShot':                  self.b_oneShot                  = val
            if key == 'b_httpResponseBodyParse':    self.b_httpResponseBodyParse    = val
            if key == 'man':                        self.str_man                    = val
            if key == 'jsonwrapper':                self.str_jsonwrapper            = val
            if key == 'useDebug':                   self.b_useDebug                 = val
            if key == 'debugFile':                  self.str_debugFile              = val
            if key == 'startFromCLI':               self._startFromCLI              = val
            if key == 'name':                       self.str_name                   = val
            if key == 'version':                    self.str_version                = val
            if key == 'verbosity':                  self.verbosity                  = int(val)
            if key == 'desc':                       self.str_desc                   = val
            if key == 'unverifiedCerts':            self.b_unverifiedCerts          = val
            if key == 'authToken':                  self.str_authToken              = val
            if key == 'httpProxy':                  self.str_httpProxy              = val

        self.dp                         = pfmisc.debug(
                                            verbosity   = self.verbosity,
                                            within      = self.__name__
                                            )

        if self.b_quiet: self.dp.verbosity = -10

        if self.b_useDebug:
            self.debug                  = Message(logTo = self.str_debugFile)
            self.debug._b_syslog        = True
            self.debug._b_flushNewLine  = True

        if len(self.str_man):
            print(self.man(on = self.str_man))
            sys.exit(0)

        if not self.b_quiet:

            self.dp.qprint(self.str_desc, level = 1)

            if self.b_useDebug:
                self.dp.qprint("""
            Debugging output is directed to the file '%s'.
                """ % (self.str_debugFile), level = 1)
            else:
                self.dp.qprint("""
            Debugging output will appear in *this* console.
                """, level = 1)

            self.dp.qprint('pfurl: Start from CLI = %d' % self._startFromCLI)
            self.dp.qprint('pfurl: Command line args = %s' % sys.argv)
            if self._startFromCLI and (sys.argv) == 1: sys.exit(1)

            str_colon_port = ''
            if self.str_port:
                str_colon_port = ':' + self.str_port

            self.dp.qprint("Will transmit to\t\t%s://%s%s" %
                (self.str_protocol, self.str_ip, str_colon_port), level = 1)

    def storage_resolveBasedOnKey(self, *args, **kwargs):
        """
        Call the remote service and ask for the storage location based on the key.

        :param args:
        :param kwargs:
        :return:
        """
        global Gd_internalvar

        d_msg       = {
            'action':   'internalctl',
            'meta': {
                'var':      'key2address',
                'compute':  '<key>'
            }
        }

        str_key     = ""
        b_status    = False

        for k,v in kwargs.items():
            if k == 'key':  str_key = v
        d_msg['meta']['key']    = str_key

        #
        d_ret = self.pullPath_core(d_msg = d_msg)

        return {
            'status':   b_status,
            'path':     str_internalLocation
        }

    def remoteLocation_resolveSimple(self, d_remote):
        """
        Resolve the remote "path" location by returning either the
        'path' or 'key' parameter in the 'remote' JSON record.

        :param d_remote:
        :return:
        """
        b_status        = False
        str_remotePath  = ""
        if 'path' in d_remote.keys():
            str_remotePath  = d_remote['path']
            b_status        = True
        if 'key' in d_remote.keys():
            str_remotePath  = d_remote['key']
            b_status        = True
        return {
            'status':   b_status,
            'path':     str_remotePath
        }

    def remoteLocation_resolve(self, d_remote):
        """
        Resolve the remote path location

        :param d_remote: the "remote" specification
        :return: a string representation of the remote path
        """
        b_status        = False
        str_remotePath  = ""
        if 'path' in d_remote.keys():
            str_remotePath  = d_remote['path']
            b_status        = True
        if 'key' in d_remote.keys():
            d_ret =  self.storage_resolveBasedOnKey(key = d_remote['key'])
            if d_ret['status']:
                b_status        = True
                str_remotePath  = d_ret['path']
        return {
            'status':   b_status,
            'path':     str_remotePath
        }

    def man(self, **kwargs):
        """
        Print some man for each understood command
        """

        str_man     = 'commands'
        str_amount  = 'full'

        for k, v in kwargs.items():
            if k == 'on':       str_man     = v
            if k == 'amount':   str_amount  = v

        if str_man == 'commands':
            str_commands = """
            This script/module provides CURL-based GET/PUT/POST communication over http
            to a remote REST-like service: """ + Colors.GREEN + """

                 ./pfurl.py [--auth <username:passwd>] [--verb <GET/POST>]   \\
                            --http <IP>[:<port>]</some/path/>

            """ + Colors.WHITE + """
            Where --auth is an optional authorization to pass to the REST API,
            --verb denotes the REST verb to use and --http specifies the REST URL.

            Additionally, a 'message' described in JSON syntax can be pushed to the
            remote service, in the following syntax: """ + Colors.GREEN + """

                 pfurl     [--auth <username:passwd>] [--verb <GET/POST>]   \\
                            --http <IP>[:<port>]</some/path/>               \\
                           [--msg <JSON-formatted-string>]

            """ + Colors.WHITE + """
            In the case of the 'pman' system this --msg flag has very specific
            contextual syntax, for example:
            """ + Colors.GREEN + """

                 pfurl      --verb POST --http %s:%s/api/v1/cmd/ --msg \\
                                '{  "action": "run",
                                    "meta": {
                                        "cmd":      "cal 7 1970",
                                        "auid":     "rudolphpienaar",
                                        "jid":      "<jid>-1",
                                        "threaded": true
                                    }
                                }'


            """ % (self.str_ip, self.str_port) + Colors.CYAN + """

            The following specific action directives are directly handled by script:
            """ + "\n" + \
            self.man_pushPath(          description =   "short")      + "\n" + \
            self.man_pullPath(          description =   "short")      + "\n" + \
            Colors.YELLOW + \
            """
            To get detailed help on any of the above commands, type
            """ + Colors.LIGHT_CYAN + \
            """
                ./pfurl.py --man <command>
            """

            return str_commands

        if str_man  == 'pushPath':  return self.man_pushPath(       description  =   str_amount)
        if str_man  == 'pullPath':  return self.man_pullPath(       description  =   str_amount)

    def man_pushPath(self, **kwargs):
        """
        """

        b_fullDescription   = False
        str_description     = "full"

        for k,v in kwargs.items():
            if k == 'description':  str_description = v
        if str_description == "full":   b_fullDescription   = True

        str_manTxt =   Colors.LIGHT_CYAN        + \
                       "\t\t%-20s" % "pushPath" + \
                       Colors.LIGHT_PURPLE      + \
                       "%-60s" % "push a filesystem path over HTTP." + \
                       Colors.NO_COLOUR

        if b_fullDescription:
            str_manTxt += """

                This pushes a file over HTTP. The 'meta' dictionary
                can be used to specify content specific information
                and other information.

                Note that the "file" server is typically *not* on the
                same port as the `pman` process. Usually a prior call
                must be made to `pman` to start a one-shot listener
                on a given port. This port then accepts the file transfer
                from the 'pushPath' method.

                The "meta" dictionary consists of several nested
                dictionaries. In particular, the "remote/path"
                field can be used to suggest a location on the remote
                filesystem to save the transmitted data. Successful
                saving to this path depends on whether or not the
                remote server process actually has permission to
                write in that location.

                """ + Colors.YELLOW + """EXAMPLE:
                """ + Colors.LIGHT_GREEN + """

                pfurl --verb POST --http %s:%s/api/v1/cmd/ --msg \\
                    '{  "action": "pushPath",
                        "meta":
                            {
                                "local":
                                    {
                                        "path":         "/path/on/client"
                                    },
                                "remote":
                                    {
                                        "path":         "/path/on/server"
                                    },
                                "transport":
                                    {
                                        "mechanism":    "compress",
                                        "compress": {
                                            "archive":  "zip",
                                            "unpack":   true,
                                            "cleanup":  true
                                        }
                                    }
                            }
                    }'
                """ % (self.str_ip, self.str_port) + Colors.NO_COLOUR  + """
                """ + Colors.YELLOW + """ALTERNATE -- using copy/symlink:
                """ + Colors.LIGHT_GREEN + """

                pfurl --verb POST --http %s:%s/api/v1/cmd/ --msg \\
                    '{  "action": "pushPath",
                        "meta":
                            {
                                "local":
                                    {
                                        "path":         "/path/on/client"
                                    },
                                "remote":
                                    {
                                        "path":         "/path/on/server"
                                    },
                                "transport":
                                    {
                                        "mechanism":    "copy",
                                        "copy": {
                                            "symlink": true
                                        }
                                    }
                            }
                    }'
                """ % (self.str_ip, self.str_port) + Colors.NO_COLOUR

        return str_manTxt

    def man_pullPath(self, **kwargs):
        """
        """

        b_fullDescription   = False
        str_description     = "full"

        for k,v in kwargs.items():
            if k == 'description':  str_description = v
        if str_description == "full":   b_fullDescription   = True

        str_manTxt =   Colors.LIGHT_CYAN        + \
                       "\t\t%-20s" % "pullPath" + \
                       Colors.LIGHT_PURPLE      + \
                       "%-60s" % "pull a filesystem path over HTTP." + \
                       Colors.NO_COLOUR

        if b_fullDescription:
            str_manTxt += """

                This pulls data over HTTP from a remote server.
                The 'meta' dictionary can be used to specify content
                specific information and other detail.

                Note that the "file" server is typically *not* on the
                same port as a `pman` process. Usually a prior call
                must be made to `pman` to start a one-shot listener
                on a given port. This port then accepts the file transfer
                from the 'pullPath' method.

                The "meta" dictionary consists of several nested
                dictionaries. In particular, the "remote/path"
                field can be used to specify a location on the remote
                filesystem to pull. Successful retrieve from this path
                depends on whether or not the remote server process actually
                has permission to read in that location.

                """ + Colors.YELLOW + """EXAMPLE -- using zip:
                """ + Colors.LIGHT_GREEN + """

                pfurl --verb POST --http %s:%s/api/v1/cmd/ --msg \\
                    '{  "action": "pullPath",
                        "meta":
                            {
                                "local":
                                    {
                                        "path":         "/path/on/client"
                                    },
                                "remote":
                                    {
                                        "path":         "/path/on/server"
                                    },
                                "transport":
                                    {
                                        "mechanism":    "compress",
                                        "compress": {
                                            "archive":  "zip",
                                            "unpack":   true,
                                            "cleanup":  true
                                        }
                                    }
                            }
                    }'
                """ % (self.str_ip, self.str_port) + Colors.NO_COLOUR + """
                """ + Colors.YELLOW + """ALTERNATE -- using copy/symlink:
                """ + Colors.LIGHT_GREEN + """

                pfurl --verb POST --http %s:%s/api/v1/cmd/ --msg \\
                    '{  "action": "pullPath",
                        "meta":
                            {
                                "local":
                                    {
                                        "path":         "/path/on/client"
                                    },
                                "remote":
                                    {
                                        "path":         "/path/on/server"
                                    },
                                "transport":
                                    {
                                        "mechanism":    "copy",
                                        "copy": {
                                            "symlink": true
                                        }
                                    }
                            }
                    }'
                """ % (self.str_ip, self.str_port) + Colors.NO_COLOUR

        return str_manTxt

    def pull_core(self, **kwargs):
        """
        Core method that interacts with the pycurl module
        """

        str_ip              = self.str_ip
        str_port            = self.str_port
        verbose             = 0
        d_msg               = {}
        str_query           = ''

        for k,v in kwargs.items():
            if k == 'ip':       str_ip      = v
            if k == 'port':     str_port    = v
            if k == 'msg':      d_msg       = v
            if k == 'verbose':  verbose     = v

        if len(d_msg):
            str_query           = '?%s' % urllib.parse.urlencode(d_msg)

        self.curl_init(verbose  = verbose)
        self.curl_URL_resolveAndSet(d_msg, str_ip, str_port, str_query)
        self.curl_unverifiedCerts_checkAndSet()

        d_ret               = self.curl_doCall()
        self.dp.qprint('Incoming transmission received, length = %s' %
                        "{:,}".format(sys.getsizeof(d_ret)),
                        level = 1,
                        comms = 'rx')
        return d_ret


    def pullPath_core(self, **kwargs):
        """
        The core 'path' pulling related processing
        """

        d_msg       = self.d_msg
        d_ret       = {}
        for k,v in kwargs.items():
            if k == 'd_msg':    d_msg   = v

        str_response = self.pull_core(msg = d_msg)

        self.dp.qprint(
            "Received "                         +
            Colors.YELLOW                       +
            "{:,}".format(len(str_response))    +
            Colors.PURPLE                       +
            " bytes...",
            level = 1,
            comms = 'status'
        )

        b_status        = False
        if isinstance(str_response, dict):
            d_response  = str_response
            b_status    = d_response['status']
            str_error   = d_response
        else:
            str_error   = str_response
        if not b_status or 'Network Error' in str_response:
            self.dp.qprint('Some error occurred at remote location:',
                        level = 1, comms ='error')
            d_ret = {
                    'status':       False,
                    'msg':          'PULL unsuccessful',
                    'response':     str_error,
                    'timestamp':    '%s' % datetime.datetime.now(),
                    'size':         "{:,}".format(len(str_response))
                    }
        else:
            d_ret = {
                    'status':       d_response['status'],
                    'msg':          'PULL successful',
                    'response':     d_response,
                    'timestamp':    '%s' % datetime.datetime.now(),
                    'size':         "{:,}".format(len(str_response))
                    }

        return d_ret

    def pullPath_compress(self, d_msg, **kwargs):
        """

        This pulls a compressed path from a remote host/location.

        Zip archives are universally unpacked to

            /tmp/unpack-<uuid.uuid4()>

        and then the file contents are moved to the actual destination
        directory. In shell, this would be:

            mkdir /tmp/unpack-<uuid.uuid4()>
            cp file.zip /tmp/unpack-<uuid.uuid4()>
            unzip /tmp/unpack-<uuid.uuid4()>/file.zip
            mv /tmp/unpack-<uuid.uuid4()>/* <destination>
            rm -fr /tmp/unpack-<uuid.uuid4()>

        """

        # Parse "header" information
        d_meta                  = d_msg['meta']

        if 'local' in d_meta:
            d_local             = d_meta['local']
        if 'to' in d_meta:
            d_local             = d_meta['to']

        str_localPath           = d_local['path']
        # d_remote                = d_meta['remote']
        d_transport             = d_meta['transport']
        d_compress              = d_transport['compress']
        d_ret                   = {
                                    'remoteServer':     {},
                                    'localOp':          {}
                                  }
        # pudb.set_trace()
        # Unpack dir stuff...
        str_uuid                = uuid.uuid4()
        str_unpackDir           = '/tmp/unpack-%s' % str_uuid
        if not os.path.isdir(str_unpackDir):
            os.makedirs(str_unpackDir)
        else:
            shutil.rmtree(str_unpackDir)
            os.makedirs(str_unpackDir)

        # Check on destination path...
        if not os.path.isdir(str_localPath):
            os.makedirs(str_localPath)

        if 'cleanup' in d_compress:
            b_cleanZip          = d_compress['cleanup']

        # Pull the actual data into a dictionary holder
        d_pull                  = self.pullPath_core()
        d_ret['remoteServer']   = d_pull
        str_response            = d_pull['response']['data']
        d_pull['response']      = '<truncated>'

        # pudb.set_trace()

        if not d_pull['status']:
            if 'stdout' in d_pull:
                return {'stdout': json.dumps(d_pull['stdout'])}
            else:
                raise Exception(d_pull['msg'])


        # str_localStem       = os.path.split(self.remoteLocation_resolveSimple(d_remote)['path'])[-1]
        str_fileSuffix      = ""
        if d_compress['archive']     == "zip":       str_fileSuffix   = ".zip"
        str_localFile       = '%s/%s' % (str_unpackDir, str_uuid) + str_fileSuffix

        self.dp.qprint("Writing byte stream to %s..." % str_localFile,
                    level = 1, comms ='status')
        with open(str_localFile, 'wb') as fh:
            try:
                fh.write(str_response)
                fh.close()
                b_status                = True
                str_msg                 = 'Write successful.'
            except:
                b_status                = False
                str_msg                 = 'Some error occurred on return payload. This usually indicates an error in the remote compute.'
        d_ret['localOp']['stream']                  = {}
        d_ret['localOp']['stream']['status']        = b_status
        d_ret['localOp']['stream']['fileWritten']   = str_localFile
        d_ret['localOp']['stream']['timestamp']     = '%s' % datetime.datetime.now()
        d_ret['localOp']['stream']['filesize']      = "{:,}".format(len(str_response))
        d_ret['localOp']['stream']['msg']           = str_msg
        d_ret['status']                             = b_status
        d_ret['msg']                                = str_msg

        if d_compress['archive'] == 'zip':
            self.dp.qprint("Unzipping %s to %s"  % (str_localFile, str_unpackDir),
                        level = 1, comms ='status')
            d_fio = zip_process(
                action          = "unzip",
                payloadFile     = str_localFile,
                path            = str_unpackDir
            )
            d_ret['localOp']['unzip']                   = d_fio
            d_ret['localOp']['unzip']['timestamp']      = '%s' % datetime.datetime.now()
            d_ret['localOp']['unzip']['filesize']       = '%s' % "{:,}".format(os.stat(d_fio['fileProcessed']).st_size)
            d_ret['status']                             = d_fio['status']
            d_ret['msg']                                = d_fio['msg']
            if d_meta['transport']['compress']['cleanup']:
                # NB: This zip file is actually in the unpack dir!
                self.dp.qprint('Removing zip file %s' % str_localFile)
                os.remove(str_localFile)

        d_ret['localOp']['move']    = {}
        # Handle case when a single file has been sent w/o zipping -- currently NON FUNCTIONAL!
        # if not d_compress['archive'] == 'zip':
        #     # str_remotePath, str_remoteFile  = os.path.split(d_remote['path'])
        #     self.dp.qprint('Moving single file %s to %s...' % (str_localFile,
        #                                                     os.path.join(str_unpackDir, str_remoteFile)))
        #     shutil.move(str_localFile, os.path.join(str_unpackDir, str_remoteFile))
        #     d_ret['localOp']['move']    = {
        #         'status':   True,
        #         'msg':      'Single file move successful.'
        #     }
        #     d_ret['status']                             = d_ret['localOp']['move']['status']
        #     d_ret['msg']                                = d_ret['localOp']['move']['msg']

        # Move file(s) to target dir
        self.dp.qprint('Moving all files in %s to %s' % (str_unpackDir, str_localPath))
        for str_file in glob.glob(str_unpackDir + '/*'):
            try:
                shutil.move(str_file, str_localPath)
                d_ret['localOp']['move']['status']  = True
                d_ret['localOp']['move']['msg']     = 'Multiple file move successful.'
                d_ret['status']                     = d_ret['localOp']['move']['status']
                d_ret['msg']                        = d_ret['localOp']['move']['msg']
            except:
                self.dp.qprint('An error occured in moving. Target might already exist.',
                                level = 1, comms ='error')
                d_ret['localOp']['move']['status']  = False
                d_ret['localOp']['move']['msg']     = 'Multiple file move unsuccessful. Target exists!'
                d_ret['status']                     = d_ret['localOp']['move']['status']
                d_ret['msg']                        = d_ret['localOp']['move']['msg']
                break

        # Clean up
        if d_meta['transport']['compress']['cleanup']:
            self.dp.qprint('Removing unpack dir %s' % str_unpackDir)
            shutil.rmtree(str_unpackDir)

        self.dp.qprint("Returning: %s" % self.pp.pformat(d_ret).strip(), level = 1, comms ='status')
        return d_ret

    def pullPath_copy(self, d_msg, **kwargs):
        """
        Handle the "copy" pull operation
        """

        # Parse "header" information
        d_meta              = d_msg['meta']
        d_local             = d_meta['local']
        str_localPath       = d_local['path']
        d_remote            = d_meta['remote']
        d_transport         = d_meta['transport']
        d_copy              = d_transport['copy']

        # Pull the actual data into a dictionary holder
        d_curl                      = {}
        d_curl['remoteServer']      = self.pullPath_core()
        d_curl['copy']              = {}
        d_curl['copy']['status']    = d_curl['remoteServer']['status']
        if not d_curl['copy']['status']:
            d_curl['copy']['msg']   = "Copy on remote server failed!"
        else:
            d_curl['copy']['msg']   = "Copy on remote server success!"

        return d_curl

    def path_remoteLocationCheck(self, d_msg, **kwargs):
        """
        This method checks if the "remote" path is valid.
        """

        # Pull the actual data into a dictionary holder
        d_pull = self.pullPath_core()
        return d_pull

    def path_localLocationCheck(self, d_msg, **kwargs):
        """
        Check if a path exists on the local filesystem

        :param self:
        :param kwargs:
        :return:
        """
        b_pull                      = False
        d_meta                      = d_msg['meta']
        if 'do' in d_meta:
            if d_meta['do'] == 'pull':
                b_pull              = True
        if 'local' in d_meta:
            d_local                 = d_meta['local']
        if 'to' in d_meta:
            d_local                 = d_meta['to']

        str_localPathFull           = d_local['path']
        str_localPath, str_unpack   = os.path.split(str_localPathFull)
        str_msg                     = ''
        str_checkedDir              = str_localPathFull

        b_isFile                    = os.path.isfile(str_localPathFull)
        b_isDir                     = os.path.isdir(str_localPathFull)
        b_exists                    = os.path.exists(str_localPathFull)

        if 'pull' in d_msg['action'] or b_pull:
            # If we are "pulling" data to local, then we assume the local
            # directory does not exist. If it does, and if 'createDir' is 'true',
            # we remove the localPath and re-create it, thus assuring it will
            # only contain the info pulled from the remote source.
            # If 'writeInExisting' is 'true', then execution continues, but
            # may fail if the pulled target exists in the localPath.

            str_checkedDir              = str_localPath
            b_isFile                    = os.path.isfile(str_localPath)
            b_isDir                     = os.path.isdir(str_localPath)
            b_exists                    = os.path.exists(str_localPath)

            if 'createDir' in d_local.keys():
                if d_local['createDir']:
                    if os.path.isdir(str_localPathFull):
                        self.dp.qprint('Removing local path %s...' % str_localPathFull)
                        shutil.rmtree(str_localPathFull)
                        str_msg         = 'Removed existing local path... '
                    self.dp.qprint('Creating empty local path %s...' % str_localPathFull)
                    os.makedirs(str_localPathFull)
                    b_exists = True
                    str_msg += 'Created new local path'
            else:
                str_msg = 'local path already exists!'
                if 'writeInExisting' in d_local.keys():
                    if not d_local['writeInExisting']:
                        if b_isDir: b_exists = False
                else:
                    if b_isDir: b_exists = False

        d_ret = {
            'action':   d_msg['action'],
            'dir':      str_checkedDir,
            'status':   b_exists,
            'isfile':   b_isFile,
            'isdir':    b_isDir,
            'msg':      str_msg
        }

        return {'check':        d_ret,
                'status':       d_ret['status'],
                'timestamp':    '%s' % datetime.datetime.now()}

    def curl_URL_resolveAndSet(self, d_msg, str_ip, str_port, str_query = ''):
        """
        Resolve the remote URL with optional port spec and set the
        corresponding curl option.
        """
        str_colon_port = ''
        if str_port:
            str_colon_port = ':' + str_port

        str_URLfull = "%s://%s%s%s%s" % \
                    (
                        self.str_protocol,
                        str_ip,
                        str_colon_port,
                        self.str_URL,
                        str_query
                    )
        self.dp.qprint(
            str_URLfull     +
            '\n '           +
            json.dumps(d_msg, indent = 4),
            comms   = 'tx')

        self.c.setopt(pycurl.URL, str_URLfull)
        return str_URLfull

    def curl_init(self, **kwargs):
        """
        Initialize the curl object and perform some
        optional header initializations as well as
        some ON/OFF settings.
        """
        verbose     = 0
        self.c      = pycurl.Curl()
        self.buffer = io.BytesIO()
        self.c.setopt(pycurl.WRITEFUNCTION,   self.buffer.write)
        self.c.setopt(pycurl.FOLLOWLOCATION,  1)
        if len(self.str_authToken):
            self.dp.qprint("Using token-based authorization <%s>" %
                            self.str_authToken)
            self.HTTPheaders.append('Authorization: bearer %s' % self.str_authToken)
        if len(self.str_contentType):
            self.HTTPheaders.append('Content-type: %s' % self.str_contentType)
        if len(self.str_auth):
            self.dp.qprint("Using user:password authentication <%s>" %
                            self.str_auth)
            self.c.setopt(pycurl.USERPWD, self.str_auth)
        if len(self.str_httpProxy):
            o_url   = urlparse(self.str_httpProxy)
            self.c.setopt(pycurl.PROXY,     o_url.hostname)
            self.c.setopt(pycurl.PROXYPORT, o_url.port)
            if o_url.scheme == 'http' or not len(o_url.scheme):
                self.c.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_HTTP)

        for k,v in kwargs.items():
            if k    == 'optON':     self.curl_setopt(optListON  = v)
            if k    == 'optOFF':    self.curl_setopt(optListOFF = v)
            if k    == 'verbose':   self.c.setopt(self.c.VERBOSE, verbose)

    def curl_fileTXModeViaForm_set(self, str_msg, str_fileToProcess):
        """
        Configure curl for file tranmission via a FORM
        """
        self.HTTPheaders.append('Mode: file')
        self.dp.qprint("Building form-based multi-part message...",
                        level = 1,
                        comms ='status')
        fread               = open(str_fileToProcess, "rb")
        filesize            = os.path.getsize(str_fileToProcess)
        self.c.setopt(
                        pycurl.HTTPPOST,
                        [
                            ("d_msg",       str_msg),
                            ("filename",    str_fileToProcess),
                            ("local",       (pycurl.FORM_FILE, str_fileToProcess))
                        ]
                    )
        self.c.setopt(pycurl.READFUNCTION,    fread.read)
        self.c.setopt(pycurl.POSTFIELDSIZE,   filesize)
        self.dp.qprint("Transmitting "                                      +
                        Colors.YELLOW                                       +
                        "{:,}".format(os.stat(str_fileToProcess).st_size)   +
                        Colors.PURPLE + " bytes...",
                        level = 1,
                        comms = 'status')

    def curl_controlMode_set(self, str_msg):
        self.HTTPheaders.append('Mode: control')
        self.dp.qprint("Sending control message...",
                        level = 1,
                        comms = 'status')
        self.c.setopt(pycurl.POSTFIELDS, str_msg)

    def curl_setopt(self, **kwargs):
        """
        Set curl object parameters.
        """
        l_optON     = []
        l_optOFF    = []
        d_opt       = {}
        for k,v in kwargs.items():
            if k == 'optListON':    l_optON     = v
            if k == 'optListOFF':   l_optOFF    = v
            if k == 'optDict':      d_opt       = v

        for on in l_optON:
            self.c.setopt(on, 1)

        for off in l_optOFF:
            self.c.setopt(off, 0)

        if d_opt:
            for k,v in d_opt.items():
                self.c.setopt(k, v)

    def curl_unverifiedCerts_checkAndSet(self):
        if self.b_unverifiedCerts:
            self.dp.qprint("Attempting an insecure connection with trusted host...")
            self.curl_setopt(d_opt  = {
                pycurl.SSL_VERIFYPEER:  0,
                pycurl.SSL_VERIFYHOST:  0
            })

    def curl_doCall(self):
        """
        Try the actual curl call and return a string response (or string
        exception)
        """
        d_ret   = {
                    'status':       False,
                    'data':         ''
                }
        self.c.setopt(pycurl.HTTPHEADER, self.HTTPheaders)
        try:
            self.c.perform()
        except Exception as e:
            str_exception       = str(e)
            self.dp.qprint('Curl perform failure error trapped: %s' %
                            str_exception,
                            comms = 'error')
            d_ret['status']     = False
            d_ret['data']       = self.buffer.getvalue()
            d_ret['exception']  = str_exception
        try:
            str_data            = self.buffer.getvalue().decode()
            d_ret['status']     = True
            try:
                d_ret['data']   = json.loads(str_data)
            except:
                d_ret['data']   = str_data
        except:
            try:
                d_ret['data']       = self.buffer.getvalue()
                d_ret['status']     = True
            except Exception as e:
                str_exception       = str(e)
                d_ret['status']     = False
                d_ret['exception']  = str_exception

        self.c.close()
        return d_ret

    def curl_responseProcess(self, d_curlResponse):
        """
        Process the curl return
        """
        d_ret   = {'status':    False}

        if d_curlResponse['status']:
            response    = d_curlResponse['data']
            if isinstance(response, dict):
                self.dp.qprint(
                        "Response from curl:\n%s" % json.dumps(response, indent = 4),
                        level   = 1,
                        comms   ='status')
            else:
                self.dp.qprint(
                        "Response from curl: %s" % response,
                        level   = 1,
                        comms   = 'status')
            if self.b_raw:
                try:
                    if self.b_httpResponseBodyParse:
                        d_ret   = json.loads(
                                self.httpResponse_bodyParse(response = response)
                        )
                    else:
                        d_ret   = json.loads(response)
                except:
                    d_ret           = response
            else:
                try:
                    d_ret['stdout']     = json.loads(response)
                except:
                    d_ret['stdout']     = response
                if 'status' in d_ret['stdout']:
                    d_ret['status']     = d_ret['stdout']['status']
                d_ret['msg']            = 'push OK.'

            if isinstance(d_ret, object):
                self.dp.qprint(json.dumps(d_ret, sort_keys=True, indent=4),
                                level   = 1,
                                comms   = 'rx')
            if isinstance(d_ret, str):
                self.dp.qprint(d_ret,
                                level   = 1,
                                comms   = 'rx')
        return d_ret

    def msg_toStr(self, d_msg):
        """
        Convert the d_msg to string and remove the outer jsonwrapper
        if it exists.
        """
        if len(self.str_jsonwrapper):
            str_msg         = json.dumps({self.str_jsonwrapper: d_msg})
        else:
            str_msg         = json.dumps(d_msg)
        return str_msg

    def push_core(self, d_msg, **kwargs):
        """
        The core logic of the communication "push" to the remote server.

        File contents are transmitted in a FORM, while meta-control type
        directives are posted in the message body directly.

        Note that most of the configuration of the curl object is handled
        by other methods (see the curl_* above).
        """

        str_fileToProcess   = ""
        d_ret               = {}
        str_ip              = self.str_ip
        str_port            = self.str_port
        verbose             = 0

        # pudb.set_trace()

        for k,v in kwargs.items():
            if k == 'fileToPush':   str_fileToProcess   = v
            if k == 'd_ret':        d_ret               = v
            if k == 'ip':           str_ip              = v
            if k == 'port':         str_port            = v
            if k == 'verbose':      verbose             = v

        str_msg             = self.msg_toStr(d_msg)
        self.curl_init(
                        optON       = [pycurl.POST],
                        verbose     = verbose
                    )

        self.curl_URL_resolveAndSet(d_msg, str_ip, str_port)
        self.curl_unverifiedCerts_checkAndSet()

        if str_fileToProcess:   self.curl_fileTXModeViaForm_set(str_msg, str_fileToProcess)
        else:                   self.curl_controlMode_set(str_msg)

        d_ret               = self.curl_responseProcess(self.curl_doCall())
        return d_ret

    def pushPath_core(self, d_msg, **kwargs):
        """
        Core logic for pushing a path (fileToProcess)
        """

        str_fileToProcess   = ""
        d_ret               = {}
        for k,v in kwargs.items():
            if k == 'fileToPush':   str_fileToProcess   = v
            if k == 'd_ret':        d_ret               = v

        d_meta              = d_msg['meta']
        str_ip              = self.str_ip
        str_port            = self.str_port
        if 'remote' in d_meta:
            d_remote            = d_meta['remote']
            if 'ip' in d_remote:    str_ip      = d_remote['ip']
            if 'port' in d_remote:  str_port    = d_remote['port']

        d_ret               = self.push_core(   d_msg,
                                                fileToPush  = str_fileToProcess,
                                                ip          = str_ip,
                                                port        = str_port
                                            )
        return d_ret

    def pushPath_compress(self, d_msg, **kwargs):
        """
        Main entry point for compressing a path (file or directory argument).

        This method contains several nested functions to improve general
        readability and maintainability.
        """

        def zip_perform():
            """
            Nested function that calls the zip_process() method to
            perform the actual zip. The return from this call is packed
            into the method 'd_ret' structure.

            Logic here handles file/dir issues, and dir naming issues (such
            as sanity checking trailing '/' chars).
            """
            nonlocal str_fileToProcess, str_zipFile, d_ret

            self.dp.qprint(
                            "Zipping target '%s'..." % str_localPath,
                            level = 1,
                            comms ='status'
            )
            str_dirSuffix   = ""
            if os.path.isdir(str_localPath):
                self.dp.qprint("target is a directory", level = 1, comms ='status')
                # Here we append a trailing '/' to the dirname so that the zip
                # operation zips the contents and not the parent dir. Note though
                # that we should only append the '/' if it is not already present!
                while str_localPath[-1] == '/':
                    str_localPath = str_localPath[0:-1]
                str_dirSuffix   = '/'
            else:
                self.dp.qprint("target is a file", level = 1, comms ='status')

            # NB NB NB! Zip functionality called here!
            d_fio   = zip_process(
                action  = 'zip',
                path    = str_localPath,
                arcroot = str_localPath + str_dirSuffix
            )

            if not d_fio['status']: return {'stdout': json.dumps(d_fio)}
            str_fileToProcess   = d_fio['fileProcessed']
            str_zipFile         = str_fileToProcess
            self.dp.qprint("Zipped to %s..." % str_fileToProcess, level = 1, comms ='status')
            d_ret['local']['zip']               = d_fio

        def zip_cleanLeftOverFiles():
            """
            Clean up leftover zip files. Files to remove are "named"
            by the zip_perform() nested function.
            """
            self.dp.qprint("Removing temp files...", level = 1, comms ='status')
            self.dp.qprint("zipFile    = %s" % str_zipFile)
            self.dp.qprint("base64File = %s" % str_base64File)
            if os.path.isfile(str_zipFile):     os.remove(str_zipFile)
            if os.path.isfile(str_base64File):  os.remove(str_base64File)

        def vars_init():
            """
            Initialize values for various method variables.

            Set values directly by binding to nonlocal variables in the
            caller scope.
            """
            nonlocal d_meta,    d_local,        d_remote,       d_transport
            nonlocal str_meta,  str_localPath,  str_archive,    str_fileToProcess
            nonlocal str_ip,    str_port
            nonlocal b_cleanZip,b_zip

            d_meta              = d_msg['meta']
            d_local             = d_meta['local']
            d_remote            = d_meta['remote']
            d_transport         = d_meta['transport']
            str_meta            = json.dumps(d_meta)
            str_localPath       = d_local['path']
            str_ip              = self.str_ip
            str_port            = self.str_port
            if 'ip' in d_remote:
                str_ip          = d_remote['ip']
            if 'port' in d_remote:
                str_port        = d_remote['port']
            if 'compress' in d_transport:
                d_compress      = d_transport['compress']
                str_archive     = d_compress['archive']
            if 'cleanup' in d_compress:
                b_cleanZip      = d_compress['cleanup']
            if str_archive      == 'zip':   b_zip   = True
            else:                           b_zip   = False
            str_fileToProcess   = str_localPath
            if os.path.isdir(str_localPath):
                b_zip           = True
                str_archive     = 'zip'

        def ret_cleanup():
            """
            Cleanup / handle the d_ret return structure.
            """
            nonlocal d_ret
            if 'status' in d_ret['remoteServer']:
                try:
                    d_ret['status'] = d_ret['remoteServer']['status']
                    d_ret['msg']    = d_ret['remoteServer']['msg']
                except:
                    self.dp.qprint("Error from server: \n%s" % d_ret,
                                    comms = 'error')
            else:
                if type(d_ret['remoteServer']) is dict:
                    d_ret['status'] = d_ret['remoteServer']['decode']['status']
                    d_ret['msg']    = d_ret['remoteServer']['decode']['msg']
                else:
                    d_ret['msg']    = "Invalid response from remote server"
                    d_ret['status'] = False
                    response  = d_ret['remoteServer']
                    d_ret['remoteServer']               = {}
                    d_ret['remoteServer']['status']     = False
                    d_ret['remoteServer']['response']   = response


        # Method code starts here

        # "Declare" variables
        d_meta          = d_transport       = {}
        d_local         = d_remote          = {}
        str_meta        = str_archive       = ""
        str_ip          = str_port          = ""
        str_localPath   = str_fileToProcess = ""
        str_zipFile     = str_base64File    = ""
        b_cleanZip      = b_zip             = False
        d_ret           = {'local': {}}

        vars_init()

        # If specified (or if the target is a directory), create zip archive
        # of the local path's contents (or the target if a file)
        if b_zip: zip_perform()

        # Push the actual file -- note the d_ret!
        d_ret['remoteServer']  = self.push_core(    d_msg,
                                                    fileToPush  = str_fileToProcess)
                                                    # d_ret       = d_ret)

        if b_cleanZip:  zip_cleanLeftOverFiles()

        self.dp.qprint("Returning: %s" % json.dumps(d_ret, indent = 4),
                        level = 1,
                        comms = 'status')

        ret_cleanup()
        return d_ret

    def pushPath_copy(self, d_msg, **kwargs):
        """
        Handle the "copy" pull operation
        """

        # Parse "header" information
        d_meta              = d_msg['meta']
        d_local             = d_meta['local']
        str_localPath       = d_local['path']
        d_remote            = d_meta['remote']
        d_transport         = d_meta['transport']
        d_copy              = d_transport['copy']

        # Pull the actual data into a dictionary holder
        d_curl                      = {
                                        'remoteServer': self.push_core(d_msg),
                                        'copy': {}
                                       }
        d_curl['copy']['status']    = d_curl['remoteServer']['status']
        if not d_curl['copy']['status']:
            d_curl['copy']['msg']   = "Copy on remote server failed!"
        else:
            d_curl['copy']['msg']   = "Copy on remote server success!"

        return d_curl

    def pathOp_do(self, d_msg, **kwargs):
        """
        Entry point for path-based push/pull calls.

        Essentially, this method is the central dispatching nexus to various
        specialized push operations.

        """

        d_meta              = d_msg['meta']
        b_OK                = True
        d_ret               = {}

        str_action          = "pull"
        for k,v, in kwargs.items():
            if k == 'action':   str_action  = v

        if not 'transport' in d_meta:
            d_transport =  {
                    "mechanism":    "compress",
                    "compress": {
                        "archive":  "zip",
                        "unpack":   True,
                        "cleanup":  True
                    }
                }
            d_meta['transport'] = d_transport
        else:
            d_transport = d_meta['transport']

        #
        # First check on the paths, both local and remote
        self.dp.qprint('Checking local path status...', level = 1, comms ='status')
        d_ret['localCheck'] = self.path_localLocationCheck(d_msg)
        if not d_ret['localCheck']['status']:
            self.dp.qprint('An error occurred while checking on the local path.',
                        level = 1, comms ='error')
            d_ret['localCheck']['msg']      = d_ret['localCheck']['check']['msg']
            d_ret['localCheck']['status']   = False
            b_OK                            = False
            self.dp.qprint("d_ret:\n%s" % self.pp.pformat(d_ret).strip(), level = 1, comms ='error')
        else:
            d_ret['localCheck']['msg']      = "Check on local path successful."
        d_ret['status']     = d_ret['localCheck']['status']
        d_ret['msg']        = d_ret['localCheck']['msg']

        if b_OK:
            d_transport['checkRemote']  = True
            self.dp.qprint('Checking remote path status...', level = 1, comms ='status')
            remoteCheck = self.path_remoteLocationCheck(d_msg)
            d_ret['remoteCheck']    = remoteCheck
            self.dp.qprint("d_ret:\n%s" % self.pp.pformat(d_ret).strip(), level = 1, comms ='rx')
            if not d_ret['remoteCheck']['status']:
                self.dp.qprint('An error occurred while checking the remote server. Sometimes using --httpResponseBodyParse will address this problem.',
                            level = 1, comms ='error')
                d_ret['remoteCheck']['msg']     = "The remote path spec is invalid!"
                b_OK                            = False
            else:
                d_ret['remoteCheck']['msg']     = "Check on remote path successful."
            d_transport['checkRemote']  = False
            d_ret['status']             = d_ret['localCheck']['status']
            d_ret['msg']                = d_ret['localCheck']['msg']

        b_jobExec           = False
        if b_OK:
            if 'compress' in d_transport and d_ret['status']:
                self.dp.qprint('Calling %s_compress()...' % str_action, level = 1, comms ='status')
                d_ret['compress']   = eval("self.%s_compress(d_msg, **kwargs)" % str_action)
                d_ret['status']     = d_ret['compress']['status']
                d_ret['msg']        = d_ret['compress']['msg']
                b_jobExec       = True

            if 'copy' in d_transport:
                self.dp.qprint('Calling %s_copy()...' % str_action, level = 1, comms ='status')
                d_ret['copyOp']     = eval("self.%s_copy(d_msg, **kwargs)" % str_action)
                d_ret['status']     = d_ret['copyOp']['copy']['status']
                d_ret['msg']        = d_ret['copyOp']['copy']['msg']
                b_jobExec       = True

        if not b_jobExec:
            d_ret['status']   = False
            d_ret['msg']      = 'No push/pull operation was performed! A filepath check failed!'

        if self.b_oneShot:
            d_ret['shutdown'] = self.server_ctlQuit(d_msg)
        return {'stdout': d_ret}

    def server_ctlQuit(self, d_msg):
        """

        :return: d_shutdown shut down JSON message from remote service.
        """

        d_shutdown      = {}
        d_meta          = d_msg['meta']
        d_meta['ctl'] = {
            'serverCmd': 'quit'
        }

        self.dp.qprint('Attempting to shut down remote server...', level = 1, comms ='status')
        try:
            # d_shutdown  = self.push_core(d_msg, fileToPush = None)
            d_shutdown  = self.push_core(d_msg)
        except:
            pass
        return d_shutdown

    def pushPath(self, d_msg, **kwargs):
        """
        Push data to a remote server using pycurl.

        Essentially, this method is the central dispatching nexus to various
        specialized push operations.

        """

        return self.pathOp_do(d_msg, action = 'push')

    def pullPath(self, d_msg, **kwargs):
        """
        Pulls data from a remote server using pycurl.

        This method assumes that a prior call has "setup" a remote fileio
        listener and has the ip:port of that instance.

        Essentially, this method is the central dispatching nexus to various
        specialized pull operations.

        :param d_msg:
        :param kwargs:
        :return:
        """

        return self.pathOp_do(d_msg, action = 'pull')

    def httpStr_parse(self, http):

        if 'http://' in http or 'https://' in http:
            protocol, address = http.split("://")
            self.str_protocol = protocol
            self.str_http         = address
        else:
            self.str_http         = http

        # Split http string into IP:port and URL
        path_split_url = self.str_http.split('/')
        str_IPport          = path_split_url[0]
        self.str_URL        = '/' + '/'.join(path_split_url[1:])
        host_port_pair = str_IPport.split(':')
        self.str_ip = host_port_pair[0]
        if len(host_port_pair) > 1:
            self.str_port = host_port_pair[1]

    def httpResponse_bodyParse(self, **kwargs):
        """
        Returns the *body* from a http response.

        :param kwargs: response = <string>
        :return: the <body> from the http <string>
        """

        str_response    = ''
        for k,v in kwargs.items():
            if k == 'response': str_response    = v
        try:
            str_body        = str_response.split('\r\n\r\n')[1]
            d_body          = yaml.load(str_body, Loader=yaml.FullLoader)
            str_body        = json.dumps(d_body)
        except:
            str_body        = str_response
        return str_body

    def __call__(self, *args, **kwargs):
        """
        Main entry point for "calling".

        :param self:
        :param kwargs:
        :return:
        """
        str_action  = ''
        http        = ''

        for key,val in kwargs.items():
            if key == 'msg':
                self.str_msg    = val
                self.d_msg      = json.loads(self.str_msg)
            if key == 'http':            self.httpStr_parse(http         = val)
            if key == 'verb':            self.str_verb              = val
            if key == 'unverifiedCerts': self.b_unverifiedCerts     = val

        if len(self.str_msg):
            if 'action' in self.d_msg: str_action  = self.d_msg['action']
            if 'path' in str_action.lower():
                d_ret = self.pathOp_do(self.d_msg, action = str_action)
            else:
                if self.str_verb == 'GET':
                    d_ret = self.pull_core(msg = self.d_msg)
                if self.str_verb == 'POST':
                    d_ret = self.push_core(self.d_msg)
            str_stdout      = json.dumps(d_ret, indent = 4, sort_keys = True)
        else:
            d_ret = self.pull_core()
            str_stdout  = '%s' % d_ret

        if not self.b_quiet: print(Colors.CYAN)
        return str_stdout

def zipdir(path, ziph, **kwargs):
    """
    Zip up a directory.

    :param path:
    :param ziph:
    :param kwargs:
    :return:
    """
    str_arcroot = ""
    for k, v in kwargs.items():
        if k == 'arcroot':  str_arcroot = v

    for root, dirs, files in os.walk(path):
        for file in files:
            str_arcfile = os.path.join(root, file)
            if len(str_arcroot):
                str_arcname = str_arcroot.split('/')[-1] + str_arcfile.split(str_arcroot)[1]
            else:
                str_arcname = str_arcfile
            try:
                ziph.write(str_arcfile, arcname = str_arcname)
            except:
                print("Skipping %s" % str_arcfile)


def zip_process(**kwargs):
    """
    Process zip operations.

    :param kwargs:
    :return:
    """

    str_localPath   = ""
    str_zipFileName = ""
    str_action      = "zip"
    str_arcroot     = ""
    for k,v in kwargs.items():
        if k == 'path':             str_localPath   = v
        if k == 'action':           str_action      = v
        if k == 'payloadFile':      str_zipFileName = v
        if k == 'arcroot':          str_arcroot     = v

    if str_action       == 'zip':
        str_mode        = 'w'
        str_zipFileName = '%s.zip' % uuid.uuid4()
    else:
        str_mode        = 'r'

    try:
        ziphandler          = zipfile.ZipFile(str_zipFileName, str_mode, zipfile.ZIP_DEFLATED)
        if str_mode == 'w':
            if os.path.isdir(str_localPath):
                zipdir(str_localPath, ziphandler, arcroot = str_arcroot)
            else:
                if len(str_arcroot):
                    str_arcname = str_arcroot.split('/')[-1] + str_localPath.split(str_arcroot)[1]
                else:
                    str_arcname = str_localPath
                try:
                    ziphandler.write(str_localPath, arcname = str_arcname)
                except:
                    ziphandler.close()
                    os.remove(str_zipFileName)
                    return {
                        'msg':      json.dumps({"msg": "No file or directory found for '%s'" % str_localPath}),
                        'status':   False
                    }
        if str_mode     == 'r':
            ziphandler.extractall(str_localPath)
        ziphandler.close()
        str_msg             = '%s operation successful' % str_action
        b_status            = True
    except:
        str_msg             = '%s operation failed'     % str_action
        b_status            = False
    return {
        'msg':              str_msg,
        'fileProcessed':    str_zipFileName,
        'status':           b_status,
        'path':             str_localPath,
        'zipmode':          str_mode,
        'filesize':         "{:,}".format(os.stat(str_zipFileName).st_size),
        'timestamp':        '%s' % datetime.datetime.now()
    }


def base64_process(**kwargs):
    """
    Process base64 file io
    """

    str_fileToSave      = ""
    str_fileToRead      = ""
    str_action          = "encode"
    data                = None

    for k,v in kwargs.items():
        if k == 'action':           str_action          = v
        if k == 'payloadBytes':     data                = v
        if k == 'payloadFile':      str_fileToRead      = v
        if k == 'saveToFile':       str_fileToSave      = v
        # if k == 'sourcePath':       str_sourcePath      = v

    if str_action       == "encode":
        # Encode the contents of the file at targetPath as ASCII for transmission
        if len(str_fileToRead):
            with open(str_fileToRead, 'rb') as f:
                data            = f.read()
                f.close()
        data_b64            = base64.b64encode(data)
        with open(str_fileToSave, 'wb') as f:
            f.write(data_b64)
            f.close()
        return {
            'msg':              'Encode successful',
            'fileProcessed':    str_fileToSave,
            'status':           True
            # 'encodedBytes':     data_b64
        }

    if str_action       == "decode":
       # if len(data) % 4:
            # not a multiple of 4, add padding:
            # data += '=' * (4 - len(data) % 4)

        # adding 3 padding = will never succumb to the TypeError and will always produce the same result.
        # https://gist.github.com/perrygeo/ee7c65bb1541ff6ac770
        bytes_decoded     = base64.b64decode(data + "===")
        with open(str_fileToSave, 'wb') as f:
            f.write(bytes_decoded)
            f.close()
        return {
            'msg':              'Decode successful',
            'fileProcessed':    str_fileToSave,
            'status':           True
            # 'decodedBytes':     bytes_decoded
        }
