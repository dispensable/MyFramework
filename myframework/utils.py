# -*- coding:utf-8 -*-

from threading import local
import os.path
import http.client
import hashlib
import base64
import pickle
import hmac
import datetime, time


version_info = (0, 1, 0)
__version__ = ".".join([str(v) for v in version_info])
FRAMEWORK = "myframwork/%s" % __version__


class LocalVar(object):
    """ descriptor for thread local response and request """
    def __init__(self):
        self.local_var = local()

    def __get__(self, instance, owner):
        if instance is None:
            return self

        try:
            return self.local_var.var
        except ValueError:
            raise ValueError('context not initialized')

    def __set__(self, instance, value):
        self.local_var.var = value

    def __delete__(self, instance):
        del self.local_var.var


class FilterDict:
    """ Filter dict descriptor for Route class """
    def __init__(self):
        self.filter = {
            'regular': r'(?P<{name}>[^/]+)',
            'int': r'(?P<{name}>[0-9]+)',
            'float': r'(?P<{name}>[0-9.]+)',
            'path': r'(?P<{name}>.+)',
        }

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return self.filter.copy()

    def __set__(self, instance, value):
        raise AttributeError('Access denied')

    def __delete__(self, instance):
        raise AttributeError('Access denied')

    def __getitem__(self, item):
        return self.filter[item]

    def __setitem__(self, key, value):
        if key in self.filter:
            raise ValueError('{!s} filter name already exists.'.format(key))
        self.filter[key] = value

    def __delitem__(self, key):
        raise AttributeError('Access denied.')

    def get(self, key, default=None):
        return self.filter.get(key, default=default)


class FileUpload:
    """ A wrapper for upload file """
    def __init__(self, fileobj, filename, formname, headers=None):
        self.file = fileobj # BytesIO or temp file
        self.filename = filename
        self.formname = formname
        self.headers = headers if headers else {}

    def get_header(self, name, default=None):
        return self.headers.get(name, default)

    def filename(self):
        return self.filename

    def _copy_file(self, tofile, chunk_size=2**16):
        file_tell = self.file.tell()
        while True:
            data = self.file.read(chunk_size)
            if not data:
                break
            tofile.write(data)
        self.file.seek(file_tell)

    def save(self, dest, overwrite=False, chunk_size=2 ** 16):
        if isinstance(dest, str):
            if os.path.isdir(dest):
                dest = os.path.join(dest, self.filename)
            if not overwrite and os.path.exists(dest):
                raise IOError('File exists')
            with open(dest, 'wb') as f:
                self._copy_file(f, chunk_size)
        elif hasattr(dest, 'write'):
            self._copy_file(dest, chunk_size)
        else:
            raise TypeError('Can not save to this obj: {!s}'.format(dest))


HTTP_CODES = http.client.responses.copy()
HTTP_CODES[418] = "I'm a teapot"
HTTP_CODES[428] = "Precondition Required"
HTTP_CODES[429] = "Too Many Requests"
HTTP_CODES[431] = "Request Header Fields Too Large"
HTTP_CODES[511] = "Network Authentication Required"
_HTTP_STATUS_LINES = dict((k, '%d %s' % (k, v))
                          for (k, v) in HTTP_CODES.items())


def sig_cookie(name, value, secret_key, secret_level=hashlib.sha256):
    msg = base64.b64encode(pickle.dumps([name, value], -1))
    sig = base64.b64encode(
        hmac.new(secret_key.encode(), msg, digestmod=secret_level).digest()
    )
    return b''.join([b'|', sig, b'?', msg]).decode()


def check_cookie(cookie, secret_key, secret_level=hashlib.sha256):
    sig_index = cookie.find('?')
    sig, msg = cookie[1: sig_index].encode(), cookie[sig_index+1:].encode()
    calculated_sig = base64.b64encode(
        hmac.new(secret_key.encode(), msg, digestmod=secret_level).digest()
    )
    return hmac.compare_digest(calculated_sig, sig)


def makelist(obj):
    if isinstance(obj, (tuple, list, set, dict)):
        return list(obj)
    elif obj:
        return [obj]
    else:
        return []


class CloseIter:
    def __init__(self, new_iter, close=None):
        self.new_iter = new_iter
        self.close_callback = makelist(close)

    def __iter__(self):
        return iter(self.new_iter)

    def close(self):
        for func in self.close_callback:
            func()


class CachedProperty:
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            value = self.func(instance)
            setattr(instance, self.func.__name__, value)
            return value


def get_rfc_time(original_time):
    return time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(original_time))


def trans_rfc_to_date_time(rfc_time):
    """
    transfer frc time to seconds since 1970
    >>> s = "Thu, 03 Oct 1997 17:15:00 GMT"
    >>> k = time.strptime(s, "%a, %d %b %Y %H:%M:%S GMT")
    >>> time.mktime(k)
    >>> 875870100.0
    """
    return time.mktime(time.strptime(rfc_time, "%a, %d %b %Y %H:%M:%S GMT"))
