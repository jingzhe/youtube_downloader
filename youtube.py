#!/usr/bin/env python
# -*- coding: utf-8 -*-

__authors__  = (
    'Ricardo Garcia Gonzalez',
    'Danny Colligan',
    'Benjamin Johnson',
    'Vasyl\' Vavrychuk',
    'Witold Baryluk',
    'Paweł Paprota',
    'Gergely Imreh',
    'Rogério Brito',
    'Philipp Hagemeister',
    'Sören Schulze',
    'Kevin Ngo',
    'Ori Avtalion',
    'shizeeg',
    )

__license__ = 'Public Domain'
__version__ = '2012.01.08b'

import cookielib
import datetime
import gzip
import htmlentitydefs
import HTMLParser
import httplib
import locale
import math
import netrc
import os
import os.path
import re
import socket
import string
import subprocess
import sys
import time
import urllib
import urllib2
import warnings
import zlib

if os.name == 'nt':
    import ctypes

try:
    import email.utils
except ImportError: # Python 2.4
    import email.Utils
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

# parse_qs was moved from the cgi module to the urlparse module recently.
try:
    from urlparse import parse_qs
except ImportError:
    from cgi import parse_qs

try:
    import lxml.etree
except ImportError:
    pass # Handled below

try:
    import xml.etree.ElementTree
except ImportError: # Python<2.5: Not officially supported, but let it slip
    warnings.warn('xml.etree.ElementTree support is missing. Consider upgrading to Python >= 2.5 if you get related errors.')

std_headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:5.0.1) Gecko/20100101 Firefox/5.0.1',
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-us,en;q=0.5',
}

import json

def preferredencoding():
    """Get preferred encoding.

    Returns the best encoding scheme for the system, based on
    locale.getpreferredencoding() and some further tweaks.
    """
    def yield_preferredencoding():
        try:
            pref = locale.getpreferredencoding()
            u'TEST'.encode(pref)
        except:
            pref = 'UTF-8'
        while True:
            yield pref
    return yield_preferredencoding().next()


def htmlentity_transform(matchobj):
    """Transforms an HTML entity to a Unicode character.

    This function receives a match object and is intended to be used with
    the re.sub() function.
    """
    entity = matchobj.group(1)

    # Known non-numeric HTML entity
    if entity in htmlentitydefs.name2codepoint:
        return unichr(htmlentitydefs.name2codepoint[entity])

    # Unicode character
    mobj = re.match(ur'(?u)#(x?\d+)', entity)
    if mobj is not None:
        numstr = mobj.group(1)
        if numstr.startswith(u'x'):
            base = 16
            numstr = u'0%s' % numstr
        else:
            base = 10
        return unichr(long(numstr, base))

    # Unknown entity in name, return its literal representation
    return (u'&%s;' % entity)


def sanitize_title(utitle):
    """Sanitizes a video title so it could be used as part of a filename."""
    utitle = re.sub(ur'(?u)&(.+?);', htmlentity_transform, utitle)
    return utitle.replace(unicode(os.sep), u'%')


def sanitize_open(filename, open_mode):
    """Try to open the given filename, and slightly tweak it if this fails.

    Attempts to open the given filename. If this fails, it tries to change
    the filename slightly, step by step, until it's either able to open it
    or it fails and raises a final exception, like the standard open()
    function.

    It returns the tuple (stream, definitive_file_name).
    """
    try:
        if filename == u'-':
            if sys.platform == 'win32':
                import msvcrt
                msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
            return (sys.stdout, filename)
        stream = open(_encodeFilename(filename), open_mode)
        return (stream, filename)
    except (IOError, OSError), err:
        # In case of error, try to remove win32 forbidden chars
        filename = re.sub(ur'[/<>:"\|\?\*]', u'#', filename)

        # An exception here should be caught in the caller
        stream = open(_encodeFilename(filename), open_mode)
        return (stream, filename)


def timeconvert(timestr):
    """Convert RFC 2822 defined time string into system timestamp"""
    timestamp = None
    timetuple = email.utils.parsedate_tz(timestr)
    if timetuple is not None:
        timestamp = email.utils.mktime_tz(timetuple)
    return timestamp

def _simplify_title(title):
    expr = re.compile(ur'[^\w\d_\-]+', flags=re.UNICODE)
    return expr.sub(u'_', title).strip(u'_')

def _orderedSet(iterable):
    """ Remove all duplicates from the input iterable """
    res = []
    for el in iterable:
        if el not in res:
            res.append(el)
    return res

def _unescapeHTML(s):
    """
    @param s a string (of type unicode)
    """
    assert type(s) == type(u'')

    htmlParser = HTMLParser.HTMLParser()
    return htmlParser.unescape(s)

def _encodeFilename(s):
    """
    @param s The name of the file (of type unicode)
    """

    assert type(s) == type(u'')
    return s.encode(sys.getfilesystemencoding(), 'ignore')

class DownloadError(Exception):
    """Download Error exception.

    This exception may be thrown by FileDownloader objects if they are not
    configured to continue on errors. They will contain the appropriate
    error message.
    """
    pass


class SameFileError(Exception):
    """Same File exception.

    This exception will be thrown by FileDownloader objects if they detect
    multiple files would have to be downloaded to the same file on disk.
    """
    pass


class PostProcessingError(Exception):
    """Post Processing exception.

    This exception may be raised by PostProcessor's .run() method to
    indicate an error in the postprocessing task.
    """
    pass

class MaxDownloadsReached(Exception):
    """ --max-downloads limit has been reached. """
    pass


class UnavailableVideoError(Exception):
    """Unavailable Format exception.

    This exception will be thrown when a video is requested
    in a format that is not available for that video.
    """
    pass


class ContentTooShortError(Exception):
    """Content Too Short exception.

    This exception may be raised by FileDownloader objects when a file they
    download is too small for what the server announced first, indicating
    the connection was probably interrupted.
    """
    # Both in bytes
    downloaded = None
    expected = None

    def __init__(self, downloaded, expected):
        self.downloaded = downloaded
        self.expected = expected


class YoutubeDLHandler(urllib2.HTTPHandler):
    """Handler for HTTP requests and responses.

    This class, when installed with an OpenerDirector, automatically adds
    the standard headers to every HTTP request and handles gzipped and
    deflated responses from web servers. If compression is to be avoided in
    a particular request, the original request in the program code only has
    to include the HTTP header "Youtubedl-No-Compression", which will be
    removed before making the real request.

    Part of this code was copied from:

    http://techknack.net/python-urllib2-handlers/

    Andrew Rowls, the author of that code, agreed to release it to the
    public domain.
    """

    @staticmethod
    def deflate(data):
        try:
            return zlib.decompress(data, -zlib.MAX_WBITS)
        except zlib.error:
            return zlib.decompress(data)

    @staticmethod
    def addinfourl_wrapper(stream, headers, url, code):
        if hasattr(urllib2.addinfourl, 'getcode'):
            return urllib2.addinfourl(stream, headers, url, code)
        ret = urllib2.addinfourl(stream, headers, url)
        ret.code = code
        return ret

    def http_request(self, req):
        for h in std_headers:
            if h in req.headers:
                del req.headers[h]
            req.add_header(h, std_headers[h])
        if 'Youtubedl-no-compression' in req.headers:
            if 'Accept-encoding' in req.headers:
                del req.headers['Accept-encoding']
            del req.headers['Youtubedl-no-compression']
        return req

    def http_response(self, req, resp):
        old_resp = resp
        # gzip
        if resp.headers.get('Content-encoding', '') == 'gzip':
            gz = gzip.GzipFile(fileobj=StringIO.StringIO(resp.read()), mode='r')
            resp = self.addinfourl_wrapper(gz, old_resp.headers, old_resp.url, old_resp.code)
            resp.msg = old_resp.msg
        # deflate
        if resp.headers.get('Content-encoding', '') == 'deflate':
            gz = StringIO.StringIO(self.deflate(resp.read()))
            resp = self.addinfourl_wrapper(gz, old_resp.headers, old_resp.url, old_resp.code)
            resp.msg = old_resp.msg
        return resp


class FileDownloader(object):
    """File Downloader class.

    File downloader objects are the ones responsible of downloading the
    actual video file and writing it to disk if the user has requested
    it, among some other tasks. In most cases there should be one per
    program. As, given a video URL, the downloader doesn't know how to
    extract all the needed information, task that InfoExtractors do, it
    has to pass the URL to one of them.

    For this, file downloader objects have a method that allows
    InfoExtractors to be registered in a given order. When it is passed
    a URL, the file downloader handles it to the first InfoExtractor it
    finds that reports being able to handle it. The InfoExtractor extracts
    all the information about the video or videos the URL refers to, and
    asks the FileDownloader to process the video information, possibly
    downloading the video.

    File downloaders accept a lot of parameters. In order not to saturate
    the object constructor with arguments, it receives a dictionary of
    options instead. These options are available through the params
    attribute for the InfoExtractors to use. The FileDownloader also
    registers itself as the downloader in charge for the InfoExtractors
    that are added to it, so this is a "mutual registration".

    Available options:

    username:         Username for authentication purposes.
    password:         Password for authentication purposes.
    usenetrc:         Use netrc for authentication instead.
    quiet:            Do not print messages to stdout.
    forceurl:         Force printing final URL.
    forcetitle:       Force printing title.
    forcethumbnail:   Force printing thumbnail URL.
    forcedescription: Force printing description.
    forcefilename:    Force printing final filename.
    simulate:         Do not download the video files.
    format:           Video format code.
    format_limit:     Highest quality format to try.
    outtmpl:          Template for output names.
    ignoreerrors:     Do not stop on download errors.
    ratelimit:        Download speed limit, in bytes/sec.
    nooverwrites:     Prevent overwriting files.
    retries:          Number of times to retry for HTTP error 5xx
    continuedl:       Try to continue downloads if possible.
    noprogress:       Do not print the progress bar.
    playliststart:    Playlist item to start at.
    playlistend:      Playlist item to end at.
    matchtitle:       Download only matching titles.
    rejecttitle:      Reject downloads for matching titles.
    logtostderr:      Log messages to stderr instead of stdout.
    consoletitle:     Display progress in console window's titlebar.
    nopart:           Do not use temporary .part files.
    updatetime:       Use the Last-modified header to set output file timestamps.
    writedescription: Write the video description to a .description file
    writeinfojson:    Write the video description to a .info.json file
    """

    params = None
    _ies = []
    _pps = []
    _download_retcode = None
    _num_downloads = None
    _screen_file = None

    def __init__(self, params):
        """Create a FileDownloader object with the given options."""
        self._ies = []
        self._pps = []
        self._download_retcode = 0
        self._num_downloads = 0
        self._screen_file = [sys.stdout, sys.stderr][params.get('logtostderr', False)]
        self.params = params

    @staticmethod
    def format_bytes(bytes):
        if bytes is None:
            return 'N/A'
        if type(bytes) is str:
            bytes = float(bytes)
        if bytes == 0.0:
            exponent = 0
        else:
            exponent = long(math.log(bytes, 1024.0))
        suffix = 'bkMGTPEZY'[exponent]
        converted = float(bytes) / float(1024 ** exponent)
        return '%.2f%s' % (converted, suffix)

    @staticmethod
    def calc_percent(byte_counter, data_len):
        if data_len is None:
            return '---.-%'
        return '%6s' % ('%3.1f%%' % (float(byte_counter) / float(data_len) * 100.0))

    @staticmethod
    def calc_eta(start, now, total, current):
        if total is None:
            return '--:--'
        dif = now - start
        if current == 0 or dif < 0.001: # One millisecond
            return '--:--'
        rate = float(current) / dif
        eta = long((float(total) - float(current)) / rate)
        (eta_mins, eta_secs) = divmod(eta, 60)
        if eta_mins > 99:
            return '--:--'
        return '%02d:%02d' % (eta_mins, eta_secs)

    @staticmethod
    def calc_speed(start, now, bytes):
        dif = now - start
        if bytes == 0 or dif < 0.001: # One millisecond
            return '%10s' % '---b/s'
        return '%10s' % ('%s/s' % FileDownloader.format_bytes(float(bytes) / dif))

    @staticmethod
    def best_block_size(elapsed_time, bytes):
        new_min = max(bytes / 2.0, 1.0)
        new_max = min(max(bytes * 2.0, 1.0), 4194304) # Do not surpass 4 MB
        if elapsed_time < 0.001:
            return long(new_max)
        rate = bytes / elapsed_time
        if rate > new_max:
            return long(new_max)
        if rate < new_min:
            return long(new_min)
        return long(rate)

    @staticmethod
    def parse_bytes(bytestr):
        """Parse a string indicating a byte quantity into a long integer."""
        matchobj = re.match(r'(?i)^(\d+(?:\.\d+)?)([kMGTPEZY]?)$', bytestr)
        if matchobj is None:
            return None
        number = float(matchobj.group(1))
        multiplier = 1024.0 ** 'bkmgtpezy'.index(matchobj.group(2).lower())
        return long(round(number * multiplier))

    def add_info_extractor(self, ie):
        """Add an InfoExtractor object to the end of the list."""
        self._ies.append(ie)
        ie.set_downloader(self)

    def add_post_processor(self, pp):
        """Add a PostProcessor object to the end of the chain."""
        self._pps.append(pp)
        pp.set_downloader(self)

    def to_screen(self, message, skip_eol=False):
        """Print message to stdout if not in quiet mode."""
        assert type(message) == type(u'')
        if not self.params.get('quiet', False):
            terminator = [u'\n', u''][skip_eol]
            output = message + terminator

            if 'b' not in self._screen_file.mode or sys.version_info[0] < 3: # Python 2 lies about the mode of sys.stdout/sys.stderr
                output = output.encode(preferredencoding(), 'ignore')
            self._screen_file.write(output)
            self._screen_file.flush()

    def to_stderr(self, message):
        """Print message to stderr."""
        print >>sys.stderr, message.encode(preferredencoding())

    def to_cons_title(self, message):
        """Set console/terminal window title to message."""
        if not self.params.get('consoletitle', False):
            return
        if os.name == 'nt' and ctypes.windll.kernel32.GetConsoleWindow():
            # c_wchar_p() might not be necessary if `message` is
            # already of type unicode()
            ctypes.windll.kernel32.SetConsoleTitleW(ctypes.c_wchar_p(message))
        elif 'TERM' in os.environ:
            sys.stderr.write('\033]0;%s\007' % message.encode(preferredencoding()))

    def fixed_template(self):
        """Checks if the output template is fixed."""
        return (re.search(ur'(?u)%\(.+?\)s', self.params['outtmpl']) is None)

    def trouble(self, message=None):
        """Determine action to take when a download problem appears.

        Depending on if the downloader has been configured to ignore
        download errors or not, this method may throw an exception or
        not when errors are found, after printing the message.
        """
        if message is not None:
            self.to_stderr(message)
        if not self.params.get('ignoreerrors', False):
            raise DownloadError(message)
        self._download_retcode = 1

    def slow_down(self, start_time, byte_counter):
        """Sleep if the download speed is over the rate limit."""
        rate_limit = self.params.get('ratelimit', None)
        if rate_limit is None or byte_counter == 0:
            return
        now = time.time()
        elapsed = now - start_time
        if elapsed <= 0.0:
            return
        speed = float(byte_counter) / elapsed
        if speed > rate_limit:
            time.sleep((byte_counter - rate_limit * (now - start_time)) / rate_limit)

    def temp_name(self, filename):
        """Returns a temporary filename for the given filename."""
        if self.params.get('nopart', False) or filename == u'-' or \
                (os.path.exists(_encodeFilename(filename)) and not os.path.isfile(_encodeFilename(filename))):
            return filename
        return filename + u'.part'

    def undo_temp_name(self, filename):
        if filename.endswith(u'.part'):
            return filename[:-len(u'.part')]
        return filename

    def try_rename(self, old_filename, new_filename):
        try:
            if old_filename == new_filename:
                return
            os.rename(_encodeFilename(old_filename), _encodeFilename(new_filename))
        except (IOError, OSError), err:
            self.trouble(u'ERROR: unable to rename file')

    def try_utime(self, filename, last_modified_hdr):
        """Try to set the last-modified time of the given file."""
        if last_modified_hdr is None:
            return
        if not os.path.isfile(_encodeFilename(filename)):
            return
        timestr = last_modified_hdr
        if timestr is None:
            return
        filetime = timeconvert(timestr)
        if filetime is None:
            return filetime
        try:
            os.utime(filename, (time.time(), filetime))
        except:
            pass
        return filetime

    def report_writedescription(self, descfn):
        """ Report that the description file is being written """
        self.to_screen(u'[info] Writing video description to: ' + descfn)

    def report_writeinfojson(self, infofn):
        """ Report that the metadata file has been written """
        self.to_screen(u'[info] Video description metadata as JSON to: ' + infofn)

    def report_destination(self, filename):
        """Report destination filename."""
        self.to_screen(u'[download] Destination: ' + filename)

    def report_progress(self, percent_str, data_len_str, speed_str, eta_str):
        """Report download progress."""
        if self.params.get('noprogress', False):
            return
        self.to_screen(u'\r[download] %s of %s at %s ETA %s' %
                (percent_str, data_len_str, speed_str, eta_str), skip_eol=True)
        self.to_cons_title(u'youtube-dl - %s of %s at %s ETA %s' %
                (percent_str.strip(), data_len_str.strip(), speed_str.strip(), eta_str.strip()))

    def report_resuming_byte(self, resume_len):
        """Report attempt to resume at given byte."""
        self.to_screen(u'[download] Resuming download at byte %s' % resume_len)

    def report_retry(self, count, retries):
        """Report retry in case of HTTP error 5xx"""
        self.to_screen(u'[download] Got server HTTP error. Retrying (attempt %d of %d)...' % (count, retries))

    def report_file_already_downloaded(self, file_name):
        """Report file has already been fully downloaded."""
        try:
            self.to_screen(u'[download] %s has already been downloaded' % file_name)
        except (UnicodeEncodeError), err:
            self.to_screen(u'[download] The file has already been downloaded')

    def report_unable_to_resume(self):
        """Report it was impossible to resume download."""
        self.to_screen(u'[download] Unable to resume')

    def report_finish(self):
        """Report download finished."""
        if self.params.get('noprogress', False):
            self.to_screen(u'[download] Download completed')
        else:
            self.to_screen(u'')

    def increment_downloads(self):
        """Increment the ordinal that assigns a number to each file."""
        self._num_downloads += 1

    def prepare_filename(self, info_dict):
        """Generate the output filename."""
        try:
            template_dict = dict(info_dict)
            template_dict['epoch'] = unicode(long(time.time()))
            template_dict['autonumber'] = unicode('%05d' % self._num_downloads)
            filename = self.params['outtmpl'] % template_dict
            return filename
        except (ValueError, KeyError), err:
            self.trouble(u'ERROR: invalid system charset or erroneous output template')
            return None

    def _match_entry(self, info_dict):
        """ Returns None iff the file should be downloaded """

        title = info_dict['title']
        matchtitle = self.params.get('matchtitle', False)
        if matchtitle and not re.search(matchtitle, title, re.IGNORECASE):
            return u'[download] "' + title + '" title did not match pattern "' + matchtitle + '"'
        rejecttitle = self.params.get('rejecttitle', False)
        if rejecttitle and re.search(rejecttitle, title, re.IGNORECASE):
            return u'"' + title + '" title matched reject pattern "' + rejecttitle + '"'
        return None

    def process_info(self, info_dict):
        """Process a single dictionary returned by an InfoExtractor."""

        reason = self._match_entry(info_dict)
        if reason is not None:
            self.to_screen(u'[download] ' + reason)
            return

        max_downloads = self.params.get('max_downloads')
        if max_downloads is not None:
            if self._num_downloads > int(max_downloads):
                raise MaxDownloadsReached()

        filename = self.prepare_filename(info_dict)

        # Forced printings
        if self.params.get('forcetitle', False):
            print info_dict['title'].encode(preferredencoding(), 'xmlcharrefreplace')
        if self.params.get('forceurl', False):
            print info_dict['url'].encode(preferredencoding(), 'xmlcharrefreplace')
        if self.params.get('forcethumbnail', False) and 'thumbnail' in info_dict:
            print info_dict['thumbnail'].encode(preferredencoding(), 'xmlcharrefreplace')
        if self.params.get('forcedescription', False) and 'description' in info_dict:
            print info_dict['description'].encode(preferredencoding(), 'xmlcharrefreplace')
        if self.params.get('forcefilename', False) and filename is not None:
            print filename.encode(preferredencoding(), 'xmlcharrefreplace')
        if self.params.get('forceformat', False):
            print info_dict['format'].encode(preferredencoding(), 'xmlcharrefreplace')

        # Do nothing else if in simulate mode
        if self.params.get('simulate', False):
            return

        if filename is None:
            return

        try:
            dn = os.path.dirname(_encodeFilename(filename))
            if dn != '' and not os.path.exists(dn): # dn is already encoded
                os.makedirs(dn)
        except (OSError, IOError), err:
            self.trouble(u'ERROR: unable to create directory ' + unicode(err))
            return

        if self.params.get('writedescription', False):
            try:
                descfn = filename + u'.description'
                self.report_writedescription(descfn)
                descfile = open(_encodeFilename(descfn), 'wb')
                try:
                    descfile.write(info_dict['description'].encode('utf-8'))
                finally:
                    descfile.close()
            except (OSError, IOError):
                self.trouble(u'ERROR: Cannot write description file ' + descfn)
                return

        if self.params.get('writeinfojson', False):
            infofn = filename + u'.info.json'
            self.report_writeinfojson(infofn)
            try:
                json.dump
            except (NameError,AttributeError):
                self.trouble(u'ERROR: No JSON encoder found. Update to Python 2.6+, setup a json module, or leave out --write-info-json.')
                return
            try:
                infof = open(_encodeFilename(infofn), 'wb')
                try:
                    json_info_dict = dict((k,v) for k,v in info_dict.iteritems() if not k in ('urlhandle',))
                    json.dump(json_info_dict, infof)
                finally:
                    infof.close()
            except (OSError, IOError):
                self.trouble(u'ERROR: Cannot write metadata to JSON file ' + infofn)
                return

        if not self.params.get('skip_download', False):
            if self.params.get('nooverwrites', False) and os.path.exists(_encodeFilename(filename)):
                success = True
            else:
                try:
                    success = self._do_download(filename, info_dict)
                except (OSError, IOError), err:
                    raise UnavailableVideoError
                except (urllib2.URLError, httplib.HTTPException, socket.error), err:
                    self.trouble(u'ERROR: unable to download video data: %s' % str(err))
                    return
                except (ContentTooShortError, ), err:
                    self.trouble(u'ERROR: content too short (expected %s bytes and served %s)' % (err.expected, err.downloaded))
                    return

            if success:
                try:
                    self.post_process(filename, info_dict)
                except (PostProcessingError), err:
                    self.trouble(u'ERROR: postprocessing: %s' % str(err))
                    return

    def download(self, url_list):
        """Download a given list of URLs."""
        print 'jingzhe download****'
        if len(url_list) > 1 and self.fixed_template():
            raise SameFileError(self.params['outtmpl'])

        for url in url_list:
            suitable_found = False
            for ie in self._ies:
                # Go to next InfoExtractor if not suitable
                if not ie.suitable(url):
                    continue

                # Suitable InfoExtractor found
                suitable_found = True

                # Extract information from URL and process it
                print 'jingzhe extract'
                ie.extract(url)

                # Suitable InfoExtractor had been found; go to next URL
                break

            if not suitable_found:
                self.trouble(u'ERROR: no suitable InfoExtractor: %s' % url)

        return self._download_retcode

    def post_process(self, filename, ie_info):
        """Run the postprocessing chain on the given file."""
        info = dict(ie_info)
        info['filepath'] = filename
        for pp in self._pps:
            info = pp.run(info)
            if info is None:
                break

    def _download_with_rtmpdump(self, filename, url, player_url):
        self.report_destination(filename)
        tmpfilename = self.temp_name(filename)

        # Check for rtmpdump first
        try:
            subprocess.call(['rtmpdump', '-h'], stdout=(file(os.path.devnull, 'w')), stderr=subprocess.STDOUT)
        except (OSError, IOError):
            self.trouble(u'ERROR: RTMP download detected but "rtmpdump" could not be run')
            return False

        # Download using rtmpdump. rtmpdump returns exit code 2 when
        # the connection was interrumpted and resuming appears to be
        # possible. This is part of rtmpdump's normal usage, AFAIK.
        basic_args = ['rtmpdump', '-q'] + [[], ['-W', player_url]][player_url is not None] + ['-r', url, '-o', tmpfilename]
        retval = subprocess.call(basic_args + [[], ['-e', '-k', '1']][self.params.get('continuedl', False)])
        while retval == 2 or retval == 1:
            prevsize = os.path.getsize(_encodeFilename(tmpfilename))
            self.to_screen(u'\r[rtmpdump] %s bytes' % prevsize, skip_eol=True)
            time.sleep(5.0) # This seems to be needed
            retval = subprocess.call(basic_args + ['-e'] + [[], ['-k', '1']][retval == 1])
            cursize = os.path.getsize(_encodeFilename(tmpfilename))
            if prevsize == cursize and retval == 1:
                break
             # Some rtmp streams seem abort after ~ 99.8%. Don't complain for those
            if prevsize == cursize and retval == 2 and cursize > 1024:
                self.to_screen(u'\r[rtmpdump] Could not download the whole video. This can happen for some advertisements.')
                retval = 0
                break
        if retval == 0:
            self.to_screen(u'\r[rtmpdump] %s bytes' % os.path.getsize(_encodeFilename(tmpfilename)))
            self.try_rename(tmpfilename, filename)
            return True
        else:
            self.trouble(u'\nERROR: rtmpdump exited with code %d' % retval)
            return False

    def _do_download(self, filename, info_dict):
        url = info_dict['url']
        player_url = info_dict.get('player_url', None)

        # Check file already present
        if self.params.get('continuedl', False) and os.path.isfile(_encodeFilename(filename)) and not self.params.get('nopart', False):
            self.report_file_already_downloaded(filename)
            return True

        # Attempt to download using rtmpdump
        if url.startswith('rtmp'):
            return self._download_with_rtmpdump(filename, url, player_url)

        print filename
        tmpfilename = self.temp_name(filename)
        print tmpfilename
        stream = None

        # Do not include the Accept-Encoding header
        headers = {'Youtubedl-no-compression': 'True'}
        basic_request = urllib2.Request(url, None, headers)
        request = urllib2.Request(url, None, headers)

        # Establish possible resume length
        if os.path.isfile(_encodeFilename(tmpfilename)):
            resume_len = os.path.getsize(_encodeFilename(tmpfilename))
        else:
            resume_len = 0

        print 'resume_len is %d' % resume_len

        open_mode = 'wb'
        if resume_len != 0:
            if self.params.get('continuedl', False):
                self.report_resuming_byte(resume_len)
                request.add_header('Range','bytes=%d-' % resume_len)
                open_mode = 'ab'
            else:
                resume_len = 0

        count = 0
        retries = self.params.get('retries', 0)
        while count <= retries:
            # Establish connection
            try:
                if count == 0 and 'urlhandle' in info_dict:
                    data = info_dict['urlhandle']
                data = urllib2.urlopen(request)
                print 'test in try'
                print request
                break
            except (urllib2.HTTPError, ), err:
                if (err.code < 500 or err.code >= 600) and err.code != 416:
                    # Unexpected HTTP error
                    raise
                elif err.code == 416:
                    # Unable to resume (requested range not satisfiable)
                    try:
                        # Open the connection again without the range header
                        data = urllib2.urlopen(basic_request)
                        print 'test is except'
                        content_length = data.info()['Content-Length']
                    except (urllib2.HTTPError, ), err:
                        if err.code < 500 or err.code >= 600:
                            raise
                    else:
                        # Examine the reported length
                        if (content_length is not None and
                                (resume_len - 100 < long(content_length) < resume_len + 100)):
                            # The file had already been fully downloaded.
                            # Explanation to the above condition: in issue #175 it was revealed that
                            # YouTube sometimes adds or removes a few bytes from the end of the file,
                            # changing the file size slightly and causing problems for some users. So
                            # I decided to implement a suggested change and consider the file
                            # completely downloaded if the file size differs less than 100 bytes from
                            # the one in the hard drive.
                            self.report_file_already_downloaded(filename)
                            self.try_rename(tmpfilename, filename)
                            return True
                        else:
                            # The length does not match, we start the download over
                            self.report_unable_to_resume()
                            open_mode = 'wb'
                            break
            # Retry
            count += 1
            if count <= retries:
                self.report_retry(count, retries)

        if count > retries:
            self.trouble(u'ERROR: giving up after %s retries' % retries)
            return False

        data_len = data.info().get('Content-length', None)
        if data_len is not None:
            data_len = long(data_len) + resume_len
        data_len_str = self.format_bytes(data_len)
        byte_counter = 0 + resume_len
        block_size = 1024
        start = time.time()
        while True:
            # Download and write
            before = time.time()
            data_block = data.read(block_size)
            after = time.time()
            if len(data_block) == 0:
                break
            byte_counter += len(data_block)

            # Open file just in time
            if stream is None:
                try:
                    (stream, tmpfilename) = sanitize_open(tmpfilename, open_mode)
                    assert stream is not None
                    filename = self.undo_temp_name(tmpfilename)
                    self.report_destination(filename)
                except (OSError, IOError), err:
                    self.trouble(u'ERROR: unable to open for writing: %s' % str(err))
                    return False
            try:
                stream.write(data_block)
            except (IOError, OSError), err:
                self.trouble(u'\nERROR: unable to write data: %s' % str(err))
                return False
            block_size = self.best_block_size(after - before, len(data_block))

            # Progress message
            speed_str = self.calc_speed(start, time.time(), byte_counter - resume_len)
            if data_len is None:
                self.report_progress('Unknown %', data_len_str, speed_str, 'Unknown ETA')
            else:
                percent_str = self.calc_percent(byte_counter, data_len)
                eta_str = self.calc_eta(start, time.time(), data_len - resume_len, byte_counter - resume_len)
                self.report_progress(percent_str, data_len_str, speed_str, eta_str)

            # Apply rate limit
            self.slow_down(start, byte_counter - resume_len)

        if stream is None:
            self.trouble(u'\nERROR: Did not get any data blocks')
            return False
        stream.close()
        self.report_finish()
        if data_len is not None and byte_counter != data_len:
            raise ContentTooShortError(byte_counter, long(data_len))
        self.try_rename(tmpfilename, filename)

        # Update file modification time
        if self.params.get('updatetime', True):
            info_dict['filetime'] = self.try_utime(filename, data.info().get('last-modified', None))

        return True


class InfoExtractor(object):
    """Information Extractor class.

    Information extractors are the classes that, given a URL, extract
    information from the video (or videos) the URL refers to. This
    information includes the real video URL, the video title and simplified
    title, author and others. The information is stored in a dictionary
    which is then passed to the FileDownloader. The FileDownloader
    processes this information possibly downloading the video to the file
    system, among other possible outcomes. The dictionaries must include
    the following fields:

    id:     Video identifier.
    url:        Final video URL.
    uploader:   Nickname of the video uploader.
    title:      Literal title.
    stitle:     Simplified title.
    ext:        Video filename extension.
    format:     Video format.
    player_url: SWF Player URL (may be None).

    The following fields are optional. Their primary purpose is to allow
    youtube-dl to serve as the backend for a video search function, such
    as the one in youtube2mp3.  They are only used when their respective
    forced printing functions are called:

    thumbnail:  Full URL to a video thumbnail image.
    description:    One-line video description.

    Subclasses of this one should re-define the _real_initialize() and
    _real_extract() methods and define a _VALID_URL regexp.
    Probably, they should also be added to the list of extractors.
    """

    _ready = False
    _downloader = None

    def __init__(self, downloader=None):
        """Constructor. Receives an optional downloader."""
        self._ready = False
        self.set_downloader(downloader)

    def suitable(self, url):
        """Receives a URL and returns True if suitable for this IE."""
        return re.match(self._VALID_URL, url) is not None

    def initialize(self):
        """Initializes an instance (authentication, etc)."""
        if not self._ready:
            self._real_initialize()
            self._ready = True

    def extract(self, url):
        """Extracts URL information and returns it in list of dicts."""
        print 'infoextractor jingzhe ***'
        self.initialize()
        return self._real_extract(url)

    def set_downloader(self, downloader):
        """Sets the downloader for this IE."""
        self._downloader = downloader

    def _real_initialize(self):
        """Real initialization process. Redefine in subclasses."""
        pass

    def _real_extract(self, url):
        """Real extraction process. Redefine in subclasses."""
        print 'base info extract'
        pass


class YoutubeIE(InfoExtractor):
    """Information extractor for youtube.com."""

    _VALID_URL = r'^((?:https?://)?(?:youtu\.be/|(?:\w+\.)?youtube(?:-nocookie)?\.com/)(?!view_play_list|my_playlists|artist|playlist)(?:(?:(?:v|embed|e)/)|(?:(?:watch(?:_popup)?(?:\.php)?)?(?:\?|#!?)(?:.+&)?v=))?)?([0-9A-Za-z_-]+)(?(1).+)?$'
    _LANG_URL = r'http://www.youtube.com/?hl=en&persist_hl=1&gl=US&persist_gl=1&opt_out_ackd=1'
    _LOGIN_URL = 'https://www.youtube.com/signup?next=/&gl=US&hl=en'
    _AGE_URL = 'http://www.youtube.com/verify_age?next_url=/&gl=US&hl=en'
    _NETRC_MACHINE = 'youtube'
    # Listed in order of quality
    _available_formats = ['38', '37', '22', '45', '35', '44', '34', '18', '43', '6', '5', '17', '13']
    _available_formats_prefer_free = ['38', '37', '45', '22', '44', '35', '43', '34', '18', '6', '5', '17', '13']
    _video_extensions = {
        '13': '3gp',
        '17': 'mp4',
        '18': 'mp4',
        '22': 'mp4',
        '37': 'mp4',
        '38': 'video', # You actually don't know if this will be MOV, AVI or whatever
        '43': 'webm',
        '44': 'webm',
        '45': 'webm',
    }
    _video_dimensions = {
        '5': '240x400',
        '6': '???',
        '13': '???',
        '17': '144x176',
        '18': '360x640',
        '22': '720x1280',
        '34': '360x640',
        '35': '480x854',
        '37': '1080x1920',
        '38': '3072x4096',
        '43': '360x640',
        '44': '480x854',
        '45': '720x1280',
    }
    IE_NAME = u'youtube'

    def report_lang(self):
        """Report attempt to set language."""
        self._downloader.to_screen(u'[youtube] Setting language')

    def report_login(self):
        """Report attempt to log in."""
        self._downloader.to_screen(u'[youtube] Logging in')

    def report_age_confirmation(self):
        """Report attempt to confirm age."""
        self._downloader.to_screen(u'[youtube] Confirming age')

    def report_video_webpage_download(self, video_id):
        """Report attempt to download video webpage."""
        self._downloader.to_screen(u'[youtube] %s: Downloading video webpage' % video_id)

    def report_video_info_webpage_download(self, video_id):
        """Report attempt to download video info webpage."""
        self._downloader.to_screen(u'[youtube] %s: Downloading video info webpage' % video_id)

    def report_information_extraction(self, video_id):
        """Report attempt to extract video information."""
        self._downloader.to_screen(u'[youtube] %s: Extracting video information' % video_id)

    def report_unavailable_format(self, video_id, format):
        """Report extracted video URL."""
        self._downloader.to_screen(u'[youtube] %s: Format %s not available' % (video_id, format))

    def report_rtmp_download(self):
        """Indicate the download will use the RTMP protocol."""
        self._downloader.to_screen(u'[youtube] RTMP download detected')

    def _print_formats(self, formats):
        print 'Available formats:'
        for x in formats:
            print '%s\t:\t%s\t[%s]' %(x, self._video_extensions.get(x, 'flv'), self._video_dimensions.get(x, '???'))

    def _real_initialize(self):
        if self._downloader is None:
            return

        # Set language
        request = urllib2.Request(self._LANG_URL)
        try:
            self.report_lang()
            urllib2.urlopen(request).read()
        except (urllib2.URLError, httplib.HTTPException, socket.error), err:
            self._downloader.to_stderr(u'WARNING: unable to set language: %s' % str(err))
            return
'''
        try:
            self.report_lang()
            proxy_support = urllib2.ProxyHandler({'http': 'http://192.168.220.5:8080'})
            opener = urllib2.build_opener(proxy_support, urllib2.HTTPHandler)
            urllib2.install_opener(opener)
            urllib2.urlopen(request).read()
        except (urllib2.URLError, httplib.HTTPException, socket.error), err:
            self._downloader.to_stderr(u'WARNING: unable to set language: %s' % str(err))
            return
'''

    def _real_extract(self, url):

        print 'in dervied class'
        # Extract video id from URL
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
            return
        video_id = mobj.group(2)
        print "video id is %s" % video_id

        # Get video webpage
        self.report_video_webpage_download(video_id)
        request = urllib2.Request('http://www.youtube.com/watch?v=%s&gl=US&hl=en&has_verified=1' % video_id)
        try:
            video_webpage = urllib2.urlopen(request).read()
        except (urllib2.URLError, httplib.HTTPException, socket.error), err:
            self._downloader.trouble(u'ERROR: unable to download video webpage: %s' % str(err))
            return

        # Attempt to extract SWF player URL
        mobj = re.search(r'swfConfig.*?"(http:\\/\\/.*?watch.*?-.*?\.swf)"', video_webpage)
        if mobj is not None:
            player_url = re.sub(r'\\(.)', r'\1', mobj.group(1))
        else:
            player_url = None

        # Get video info
        self.report_video_info_webpage_download(video_id)
        for el_type in ['&el=embedded', '&el=detailpage', '&el=vevo', '']:
            video_info_url = ('http://www.youtube.com/get_video_info?&video_id=%s%s&ps=default&eurl=&gl=US&hl=en'
                    % (video_id, el_type))
            request = urllib2.Request(video_info_url)
            try:
                video_info_webpage = urllib2.urlopen(request).read()
                video_info = parse_qs(video_info_webpage)
                if 'token' in video_info:
                    break
            except (urllib2.URLError, httplib.HTTPException, socket.error), err:
                self._downloader.trouble(u'ERROR: unable to download video info webpage: %s' % str(err))
                return
        if 'token' not in video_info:
            if 'reason' in video_info:
                self._downloader.trouble(u'ERROR: YouTube said: %s' % video_info['reason'][0].decode('utf-8'))
            else:
                self._downloader.trouble(u'ERROR: "token" parameter not in video info for unknown reason')
            return

        # Start extracting information
        self.report_information_extraction(video_id)

        # uploader
        if 'author' not in video_info:
            self._downloader.trouble(u'ERROR: unable to extract uploader nickname')
            return
        video_uploader = urllib.unquote_plus(video_info['author'][0])

        # title
        if 'title' not in video_info:
            self._downloader.trouble(u'ERROR: unable to extract video title')
            return
        video_title = urllib.unquote_plus(video_info['title'][0])
        video_title = video_title.decode('utf-8')
        video_title = sanitize_title(video_title)

        # simplified title
        simple_title = _simplify_title(video_title)

        # thumbnail image
        if 'thumbnail_url' not in video_info:
            self._downloader.trouble(u'WARNING: unable to extract video thumbnail')
            video_thumbnail = ''
        else:   # don't panic if we can't find it
            video_thumbnail = urllib.unquote_plus(video_info['thumbnail_url'][0])

        # upload date
        upload_date = u'NA'
        mobj = re.search(r'id="eow-date.*?>(.*?)</span>', video_webpage, re.DOTALL)
        if mobj is not None:
            upload_date = ' '.join(re.sub(r'[/,-]', r' ', mobj.group(1)).split())
            format_expressions = ['%d %B %Y', '%B %d %Y', '%b %d %Y']
            for expression in format_expressions:
                try:
                    upload_date = datetime.datetime.strptime(upload_date, expression).strftime('%Y%m%d')
                except:
                    pass

        # description
        try:
            lxml.etree
        except NameError:
            video_description = u'No description available.'
            if self._downloader.params.get('forcedescription', False) or self._downloader.params.get('writedescription', False):
                mobj = re.search(r'<meta name="description" content="(.*)"(?:\s*/)?>', video_webpage)
                if mobj is not None:
                    video_description = mobj.group(1).decode('utf-8')
        else:
            html_parser = lxml.etree.HTMLParser(encoding='utf-8')
            vwebpage_doc = lxml.etree.parse(StringIO.StringIO(video_webpage), html_parser)
            video_description = u''.join(vwebpage_doc.xpath('id("eow-description")//text()'))
            # TODO use another parser

        # token
        video_token = urllib.unquote_plus(video_info['token'][0])

        # Decide which formats to download
        req_format = self._downloader.params.get('format', None)

        if 'conn' in video_info and video_info['conn'][0].startswith('rtmp'):
            self.report_rtmp_download()
            video_url_list = [(None, video_info['conn'][0])]
        elif 'url_encoded_fmt_stream_map' in video_info and len(video_info['url_encoded_fmt_stream_map']) >= 1:
            url_data_strs = video_info['url_encoded_fmt_stream_map'][0].split(',')
            url_data = [parse_qs(uds) for uds in url_data_strs]
            url_data = filter(lambda ud: 'itag' in ud and 'url' in ud, url_data)
            url_map = dict((ud['itag'][0], ud['url'][0]) for ud in url_data)

            format_limit = self._downloader.params.get('format_limit', None)
            available_formats = self._available_formats_prefer_free if self._downloader.params.get('prefer_free_formats', False) else self._available_formats
            if format_limit is not None and format_limit in available_formats:
                format_list = available_formats[available_formats.index(format_limit):]
            else:
                format_list = available_formats
            existing_formats = [x for x in format_list if x in url_map]
            if len(existing_formats) == 0:
                self._downloader.trouble(u'ERROR: no known formats available for video')
                return
            if self._downloader.params.get('listformats', None):
                self._print_formats(existing_formats)
                return
            if req_format is None or req_format == 'best':
                video_url_list = [(existing_formats[0], url_map[existing_formats[0]])] # Best quality
            elif req_format == 'worst':
                video_url_list = [(existing_formats[len(existing_formats)-1], url_map[existing_formats[len(existing_formats)-1]])] # worst quality
            elif req_format in ('-1', 'all'):
                video_url_list = [(f, url_map[f]) for f in existing_formats] # All formats
            else:
                # Specific formats. We pick the first in a slash-delimeted sequence.
                # For example, if '1/2/3/4' is requested and '2' and '4' are available, we pick '2'.
                req_formats = req_format.split('/')
                video_url_list = None
                for rf in req_formats:
                    if rf in url_map:
                        video_url_list = [(rf, url_map[rf])]
                        break
                if video_url_list is None:
                    self._downloader.trouble(u'ERROR: requested format not available')
                    return
        else:
            self._downloader.trouble(u'ERROR: no conn or url_encoded_fmt_stream_map information found in video info')
            return

        for format_param, video_real_url in video_url_list:
            # At this point we have a new video
            self._downloader.increment_downloads()

            # Extension
            video_extension = self._video_extensions.get(format_param, 'flv')

            try:
                # Process video information
                self._downloader.process_info({
                    'id':       video_id.decode('utf-8'),
                    'url':      video_real_url.decode('utf-8'),
                    'uploader': video_uploader.decode('utf-8'),
                    'upload_date':  upload_date,
                    'title':    video_title,
                    'stitle':   simple_title,
                    'ext':      video_extension.decode('utf-8'),
                    'format':   (format_param is None and u'NA' or format_param.decode('utf-8')),
                    'thumbnail':    video_thumbnail.decode('utf-8'),
                    'description':  video_description,
                    'player_url':   player_url,
                })
            except UnavailableVideoError, err:
                self._downloader.trouble(u'\nERROR: unable to download video')


class PostProcessor(object):
    """Post Processor class.

    PostProcessor objects can be added to downloaders with their
    add_post_processor() method. When the downloader has finished a
    successful download, it will take its internal chain of PostProcessors
    and start calling the run() method on each one of them, first with
    an initial argument and then with the returned value of the previous
    PostProcessor.

    The chain will be stopped if one of them ever returns None or the end
    of the chain is reached.

    PostProcessor objects follow a "mutual registration" process similar
    to InfoExtractor objects.
    """

    _downloader = None

    def __init__(self, downloader=None):
        self._downloader = downloader

    def set_downloader(self, downloader):
        """Sets the downloader for this PP."""
        self._downloader = downloader

    def run(self, information):
        """Run the PostProcessor.

        The "information" argument is a dictionary like the ones
        composed by InfoExtractors. The only difference is that this
        one has an extra field called "filepath" that points to the
        downloaded file.

        When this method returns None, the postprocessing chain is
        stopped. However, this method may return an information
        dictionary that will be passed to the next postprocessing
        object in the chain. It can be the one it received after
        changing some fields.

        In addition, this method may raise a PostProcessingError
        exception that will be taken into account by the downloader
        it was called from.
        """
        return information # by default, do nothing

class AudioConversionError(BaseException):
    def __init__(self, message):
        self.message = message

class FFmpegExtractAudioPP(PostProcessor):

    def __init__(self, downloader=None, preferredcodec=None, preferredquality=None, keepvideo=False):
        PostProcessor.__init__(self, downloader)
        if preferredcodec is None:
            preferredcodec = 'best'
        self._preferredcodec = preferredcodec
        self._preferredquality = preferredquality
        self._keepvideo = keepvideo

    @staticmethod
    def get_audio_codec(path):
        try:
            cmd = ['ffprobe', '-show_streams', '--', _encodeFilename(path)]
            handle = subprocess.Popen(cmd, stderr=file(os.path.devnull, 'w'), stdout=subprocess.PIPE)
            output = handle.communicate()[0]
            if handle.wait() != 0:
                return None
        except (IOError, OSError):
            return None
        audio_codec = None
        for line in output.split('\n'):
            if line.startswith('codec_name='):
                audio_codec = line.split('=')[1].strip()
            elif line.strip() == 'codec_type=audio' and audio_codec is not None:
                return audio_codec
        return None

    @staticmethod
    def run_ffmpeg(path, out_path, codec, more_opts):
        if codec is None:
            acodec_opts = []
        else:
            acodec_opts = ['-acodec', codec]
        cmd = ['ffmpeg', '-y', '-i', _encodeFilename(path), '-vn'] + acodec_opts + more_opts + ['--', _encodeFilename(out_path)]
        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout,stderr = p.communicate()
        except (IOError, OSError):
            e = sys.exc_info()[1]
            if isinstance(e, OSError) and e.errno == 2:
                raise AudioConversionError('ffmpeg not found. Please install ffmpeg.')
            else:
                raise e
        if p.returncode != 0:
            msg = stderr.strip().split('\n')[-1]
            raise AudioConversionError(msg)

    def run(self, information):
        path = information['filepath']

        filecodec = self.get_audio_codec(path)
        if filecodec is None:
            self._downloader.to_stderr(u'WARNING: unable to obtain file audio codec with ffprobe')
            return None

        more_opts = []
        if self._preferredcodec == 'best' or self._preferredcodec == filecodec or (self._preferredcodec == 'm4a' and filecodec == 'aac'):
            if self._preferredcodec == 'm4a' and filecodec == 'aac':
                # Lossless, but in another container
                acodec = 'copy'
                extension = self._preferredcodec
                more_opts = ['-absf', 'aac_adtstoasc']
            elif filecodec in ['aac', 'mp3', 'vorbis']:
                # Lossless if possible
                acodec = 'copy'
                extension = filecodec
                if filecodec == 'aac':
                    more_opts = ['-f', 'adts']
                if filecodec == 'vorbis':
                    extension = 'ogg'
            else:
                # MP3 otherwise.
                acodec = 'libmp3lame'
                extension = 'mp3'
                more_opts = []
                if self._preferredquality is not None:
                    more_opts += ['-ab', self._preferredquality]
        else:
            # We convert the audio (lossy)
            acodec = {'mp3': 'libmp3lame', 'aac': 'aac', 'm4a': 'aac', 'vorbis': 'libvorbis', 'wav': None}[self._preferredcodec]
            extension = self._preferredcodec
            more_opts = []
            if self._preferredquality is not None:
                more_opts += ['-ab', self._preferredquality]
            if self._preferredcodec == 'aac':
                more_opts += ['-f', 'adts']
            if self._preferredcodec == 'm4a':
                more_opts += ['-absf', 'aac_adtstoasc']
            if self._preferredcodec == 'vorbis':
                extension = 'ogg'
            if self._preferredcodec == 'wav':
                extension = 'wav'
                more_opts += ['-f', 'wav']

        prefix, sep, ext = path.rpartition(u'.') # not os.path.splitext, since the latter does not work on unicode in all setups
        new_path = prefix + sep + extension
        self._downloader.to_screen(u'[ffmpeg] Destination: ' + new_path)
        try:
            self.run_ffmpeg(path, new_path, acodec, more_opts)
        except:
            etype,e,tb = sys.exc_info()
            if isinstance(e, AudioConversionError):
                self._downloader.to_stderr(u'ERROR: audio conversion failed: ' + e.message)
            else:
                self._downloader.to_stderr(u'ERROR: error running ffmpeg')
            return None

        # Try to update the date time for extracted audio file.
        if information.get('filetime') is not None:
            try:
                os.utime(_encodeFilename(new_path), (time.time(), information['filetime']))
            except:
                self._downloader.to_stderr(u'WARNING: Cannot update utime of audio file')

        if not self._keepvideo:
            try:
                os.remove(_encodeFilename(path))
            except (IOError, OSError):
                self._downloader.to_stderr(u'WARNING: Unable to remove downloaded video file')
                return None

        information['filepath'] = new_path
        return information


def parseOpts():
    # Deferred imports
    import getpass
    import optparse
    import shlex

    def _format_option_string(option):
        ''' ('-o', '--option') -> -o, --format METAVAR'''

        opts = []

        if option._short_opts: opts.append(option._short_opts[0])
        if option._long_opts: opts.append(option._long_opts[0])
        if len(opts) > 1: opts.insert(1, ', ')

        if option.takes_value(): opts.append(' %s' % option.metavar)

        return "".join(opts)


    max_width = 80
    max_help_position = 80

    fmt = optparse.IndentedHelpFormatter(width=max_width, max_help_position=max_help_position)
    fmt.format_option_strings = _format_option_string

    kw = {
        'version'   : __version__,
        'formatter' : fmt,
        'usage' : '%prog [options] url [url...]',
        'conflict_handler' : 'resolve',
    }

    parser = optparse.OptionParser(**kw)

    # option groups
    general        = optparse.OptionGroup(parser, 'General Options')
    selection      = optparse.OptionGroup(parser, 'Video Selection')
    authentication = optparse.OptionGroup(parser, 'Authentication Options')
    video_format   = optparse.OptionGroup(parser, 'Video Format Options')
    postproc       = optparse.OptionGroup(parser, 'Post-processing Options')
    filesystem     = optparse.OptionGroup(parser, 'Filesystem Options')
    verbosity      = optparse.OptionGroup(parser, 'Verbosity / Simulation Options')

    general.add_option('-h', '--help',
            action='help', help='print this help text and exit')
    general.add_option('-v', '--version',
            action='version', help='print program version and exit')
    general.add_option('-i', '--ignore-errors',
            action='store_true', dest='ignoreerrors', help='continue on download errors', default=False)
    general.add_option('-r', '--rate-limit',
            dest='ratelimit', metavar='LIMIT', help='download rate limit (e.g. 50k or 44.6m)')
    general.add_option('-R', '--retries',
            dest='retries', metavar='RETRIES', help='number of retries (default is 10)', default=10)
    general.add_option('--dump-user-agent',
            action='store_true', dest='dump_user_agent',
            help='display the current browser identification', default=False)
    general.add_option('--list-extractors',
            action='store_true', dest='list_extractors',
            help='List all supported extractors and the URLs they would handle', default=False)

    selection.add_option('--playlist-start',
            dest='playliststart', metavar='NUMBER', help='playlist video to start at (default is 1)', default=1)
    selection.add_option('--playlist-end',
            dest='playlistend', metavar='NUMBER', help='playlist video to end at (default is last)', default=-1)
    selection.add_option('--match-title', dest='matchtitle', metavar='REGEX',help='download only matching titles (regex or caseless sub-string)')
    selection.add_option('--reject-title', dest='rejecttitle', metavar='REGEX',help='skip download for matching titles (regex or caseless sub-string)')
    selection.add_option('--max-downloads', metavar='NUMBER', dest='max_downloads', help='Abort after downloading NUMBER files', default=None)

    video_format.add_option('-f', '--format',
            action='store', dest='format', metavar='FORMAT', help='video format code')
    video_format.add_option('--all-formats',
            action='store_const', dest='format', help='download all available video formats', const='all')
    video_format.add_option('--prefer-free-formats',
            action='store_true', dest='prefer_free_formats', default=False, help='prefer free video formats unless a specific one is requested')
    video_format.add_option('--max-quality',
            action='store', dest='format_limit', metavar='FORMAT', help='highest quality format to download')
    video_format.add_option('-F', '--list-formats',
            action='store_true', dest='listformats', help='list all available formats (currently youtube only)')


    verbosity.add_option('-q', '--quiet',
            action='store_true', dest='quiet', help='activates quiet mode', default=False)
    verbosity.add_option('-s', '--simulate',
            action='store_true', dest='simulate', help='do not download the video and do not write anything to disk', default=False)
    verbosity.add_option('--skip-download',
            action='store_true', dest='skip_download', help='do not download the video', default=False)
    verbosity.add_option('-g', '--get-url',
            action='store_true', dest='geturl', help='simulate, quiet but print URL', default=False)
    verbosity.add_option('-e', '--get-title',
            action='store_true', dest='gettitle', help='simulate, quiet but print title', default=False)
    verbosity.add_option('--get-thumbnail',
            action='store_true', dest='getthumbnail',
            help='simulate, quiet but print thumbnail URL', default=False)
    verbosity.add_option('--get-description',
            action='store_true', dest='getdescription',
            help='simulate, quiet but print video description', default=False)
    verbosity.add_option('--get-filename',
            action='store_true', dest='getfilename',
            help='simulate, quiet but print output filename', default=False)
    verbosity.add_option('--get-format',
            action='store_true', dest='getformat',
            help='simulate, quiet but print output format', default=False)
    verbosity.add_option('--no-progress',
            action='store_true', dest='noprogress', help='do not print progress bar', default=False)
    verbosity.add_option('--console-title',
            action='store_true', dest='consoletitle',
            help='display progress in console titlebar', default=False)


    filesystem.add_option('-t', '--title',
            action='store_true', dest='usetitle', help='use title in file name', default=False)
    filesystem.add_option('-l', '--literal',
            action='store_true', dest='useliteral', help='use literal title in file name', default=False)
    filesystem.add_option('-A', '--auto-number',
            action='store_true', dest='autonumber',
            help='number downloaded files starting from 00000', default=False)
    filesystem.add_option('-o', '--output',
            dest='outtmpl', metavar='TEMPLATE', help='output filename template. Use %(stitle)s to get the title, %(uploader)s for the uploader name, %(autonumber)s to get an automatically incremented number, %(ext)s for the filename extension, %(upload_date)s for the upload date (YYYYMMDD), and %% for a literal percent. Use - to output to stdout.')
    filesystem.add_option('-a', '--batch-file',
            dest='batchfile', metavar='FILE', help='file containing URLs to download (\'-\' for stdin)')
    filesystem.add_option('-w', '--no-overwrites',
            action='store_true', dest='nooverwrites', help='do not overwrite files', default=False)
    filesystem.add_option('-c', '--continue',
            action='store_true', dest='continue_dl', help='resume partially downloaded files', default=False)
    filesystem.add_option('--no-continue',
            action='store_false', dest='continue_dl',
            help='do not resume partially downloaded files (restart from beginning)')
    filesystem.add_option('--cookies',
            dest='cookiefile', metavar='FILE', help='file to read cookies from and dump cookie jar in')
    filesystem.add_option('--no-part',
            action='store_true', dest='nopart', help='do not use .part files', default=False)
    filesystem.add_option('--no-mtime',
            action='store_false', dest='updatetime',
            help='do not use the Last-modified header to set the file modification time', default=True)
    filesystem.add_option('--write-description',
            action='store_true', dest='writedescription',
            help='write video description to a .description file', default=False)
    filesystem.add_option('--write-info-json',
            action='store_true', dest='writeinfojson',
            help='write video metadata to a .info.json file', default=False)


    postproc.add_option('--extract-audio', action='store_true', dest='extractaudio', default=False,
            help='convert video files to audio-only files (requires ffmpeg and ffprobe)')
    postproc.add_option('--audio-format', metavar='FORMAT', dest='audioformat', default='best',
            help='"best", "aac", "vorbis", "mp3", "m4a", or "wav"; best by default')
    postproc.add_option('--audio-quality', metavar='QUALITY', dest='audioquality', default='128K',
            help='ffmpeg audio bitrate specification, 128k by default')
    postproc.add_option('-k', '--keep-video', action='store_true', dest='keepvideo', default=False,
            help='keeps the video file on disk after the post-processing; the video is erased by default')


    parser.add_option_group(general)
    parser.add_option_group(selection)
    parser.add_option_group(filesystem)
    parser.add_option_group(verbosity)
    parser.add_option_group(video_format)
    parser.add_option_group(authentication)
    parser.add_option_group(postproc)

    argv = sys.argv[1:]
    opts, args = parser.parse_args(argv)

    return parser, opts, args

def gen_extractors():
    """ Return a list of an instance of every supported extractor.
    The order does matter; the first extractor matched is the one handling the URL.
    """
    youtube_ie = YoutubeIE()
    return [
        youtube_ie,
    ]

def _real_main():
    print 'in _real_main'
    parser, opts, args = parseOpts()
    print 'args is: '
    print args


    # Open appropriate CookieJar
    if opts.cookiefile is None:
        jar = cookielib.CookieJar()
        print 'cookie is none'
    else:
        print 'cookie is not none'
        try:
            jar = cookielib.MozillaCookieJar(opts.cookiefile)
            if os.path.isfile(opts.cookiefile) and os.access(opts.cookiefile, os.R_OK):
                jar.load()
        except (IOError, OSError), err:
            sys.exit(u'ERROR: unable to open cookie file')

    # Dump user agent
    if opts.dump_user_agent:
        print std_headers['User-Agent']
        sys.exit(0)

    # Batch file verification
    batchurls = []
    if opts.batchfile is not None:
        try:
            if opts.batchfile == '-':
                batchfd = sys.stdin
            else:
                batchfd = open(opts.batchfile, 'r')
            batchurls = batchfd.readlines()
            batchurls = [x.strip() for x in batchurls]
            batchurls = [x for x in batchurls if len(x) > 0 and not re.search(r'^[#/;]', x)]
        except IOError:
            sys.exit(u'ERROR: batch file could not be read')
    all_urls = batchurls + args

    # General configuration
    cookie_processor = urllib2.HTTPCookieProcessor(jar)
    opener = urllib2.build_opener(urllib2.ProxyHandler(), cookie_processor, YoutubeDLHandler())
    urllib2.install_opener(opener)
    socket.setdefaulttimeout(300) # 5 minutes should be enough (famous last words)

    extractors = gen_extractors()
    print extractors

    if opts.list_extractors:
        for ie in extractors:
            print 'jingzhe 1'
            print(ie.IE_NAME)
            print(all_urls)
            matchedUrls = filter(lambda url: ie.suitable(url), all_urls)
            all_urls = filter(lambda url: url not in matchedUrls, all_urls)
            for mu in matchedUrls:
                print('matchedUrls:')
                print(u'  ' + mu)
        sys.exit(0)

    # Conflicting, missing and erroneous options
    if opts.outtmpl is not None and (opts.useliteral or opts.usetitle or opts.autonumber):
        parser.error(u'using output template conflicts with using title, literal title or auto number')
    if opts.usetitle and opts.useliteral:
        parser.error(u'using title conflicts with using literal title')
    if opts.ratelimit is not None:
        numeric_limit = FileDownloader.parse_bytes(opts.ratelimit)
        if numeric_limit is None:
            parser.error(u'invalid rate limit specified')
        opts.ratelimit = numeric_limit
    if opts.retries is not None:
        try:
            opts.retries = long(opts.retries)
        except (TypeError, ValueError), err:
            parser.error(u'invalid retry count specified')
    try:
        opts.playliststart = int(opts.playliststart)
        if opts.playliststart <= 0:
            raise ValueError(u'Playlist start must be positive')
    except (TypeError, ValueError), err:
        parser.error(u'invalid playlist start number specified')
    try:
        opts.playlistend = int(opts.playlistend)
        if opts.playlistend != -1 and (opts.playlistend <= 0 or opts.playlistend < opts.playliststart):
            raise ValueError(u'Playlist end must be greater than playlist start')
    except (TypeError, ValueError), err:
        parser.error(u'invalid playlist end number specified')
    if opts.extractaudio:
        if opts.audioformat not in ['best', 'aac', 'mp3', 'vorbis', 'm4a', 'wav']:
            parser.error(u'invalid audio format specified')

    # File downloader
    fd = FileDownloader({
        'quiet': (opts.quiet or opts.geturl or opts.gettitle or opts.getthumbnail or opts.getdescription or opts.getfilename or opts.getformat),
        'forceurl': opts.geturl,
        'forcetitle': opts.gettitle,
        'forcethumbnail': opts.getthumbnail,
        'forcedescription': opts.getdescription,
        'forcefilename': opts.getfilename,
        'forceformat': opts.getformat,
        'simulate': opts.simulate,
        'skip_download': (opts.skip_download or opts.simulate or opts.geturl or opts.gettitle or opts.getthumbnail or opts.getdescription or opts.getfilename or opts.getformat),
        'format': opts.format,
        'format_limit': opts.format_limit,
        'listformats': opts.listformats,
        'outtmpl': ((opts.outtmpl is not None and opts.outtmpl.decode(preferredencoding()))
            or (opts.format == '-1' and opts.usetitle and u'%(stitle)s-%(id)s-%(format)s.%(ext)s')
            or (opts.format == '-1' and opts.useliteral and u'%(title)s-%(id)s-%(format)s.%(ext)s')
            or (opts.format == '-1' and u'%(id)s-%(format)s.%(ext)s')
            or (opts.usetitle and opts.autonumber and u'%(autonumber)s-%(stitle)s-%(id)s.%(ext)s')
            or (opts.useliteral and opts.autonumber and u'%(autonumber)s-%(title)s-%(id)s.%(ext)s')
            or (opts.usetitle and u'%(stitle)s-%(id)s.%(ext)s')
            or (opts.useliteral and u'%(title)s-%(id)s.%(ext)s')
            or (opts.autonumber and u'%(autonumber)s-%(id)s.%(ext)s')
            or u'%(id)s.%(ext)s'),
        'ignoreerrors': opts.ignoreerrors,
        'ratelimit': opts.ratelimit,
        'nooverwrites': opts.nooverwrites,
        'retries': opts.retries,
        'continuedl': opts.continue_dl,
        'noprogress': opts.noprogress,
        'playliststart': opts.playliststart,
        'playlistend': opts.playlistend,
        'logtostderr': opts.outtmpl == '-',
        'consoletitle': opts.consoletitle,
        'nopart': opts.nopart,
        'updatetime': opts.updatetime,
        'writedescription': opts.writedescription,
        'writeinfojson': opts.writeinfojson,
        'matchtitle': opts.matchtitle,
        'rejecttitle': opts.rejecttitle,
        'max_downloads': opts.max_downloads,
        'prefer_free_formats': opts.prefer_free_formats,
        })
    for extractor in extractors:
        fd.add_info_extractor(extractor)

    # PostProcessors
    if opts.extractaudio:
        fd.add_post_processor(FFmpegExtractAudioPP(preferredcodec=opts.audioformat, preferredquality=opts.audioquality, keepvideo=opts.keepvideo))

    # Maybe do nothing
    if len(all_urls) < 1:
        if not opts.update_self:
            parser.error(u'you must provide at least one URL')
        else:
            sys.exit()

    try:
        retcode = fd.download(all_urls)
    except MaxDownloadsReached:
        fd.to_screen(u'--max-download limit reached, aborting.')
        retcode = 101

    # Dump cookie jar if requested
    if opts.cookiefile is not None:
        try:
            jar.save()
        except (IOError, OSError), err:
            sys.exit(u'ERROR: unable to save cookie jar')

    sys.exit(retcode)

def main():
    try:
        _real_main()
    except DownloadError:
        sys.exit(1)
    except SameFileError:
        sys.exit(u'ERROR: fixed output name but more than one file to download')
    except KeyboardInterrupt:
        sys.exit(u'\nERROR: Interrupted by user')

if __name__ == '__main__':
    main()

# vim: set ts=4 sw=4 sts=4 noet ai si filetype=python:
