import hashlib
from cgi import FieldStorage
from http.cookies import SimpleCookie
from io import BytesIO
from json import load, JSONDecodeError
from tempfile import TemporaryFile
from urllib import parse

from myframework.error import HttpError
from .utils import FileUpload
from .utils import LocalVar
from .utils import check_cookie


class Request(object):
    """ A WSGI environ warper so we can easily access request property"""

    MEMFILE_MAX = 102400

    def __init__(self, environ=None):
        self.environ = {} if environ is None else environ
        self.environ['myframework.request'] = self

    @property
    def path(self):
        return self.environ['PATH_INFO']

    @property
    def headers(self):
        headers = {}
        headers['content-length'] = self.environ.get('CONTENT-LENGTH', '')
        headers['content-type'] = self.environ.get('CONTENT-TYPE', '')
        for key in self.environ:
            if key.startswith('HTTP_'):
                headers[key[5:].lower()] = self.environ[key]
        return headers

    @property
    def cookie(self):
        """ 返回SIMPLECOOKIE生成的SimpleCookie实例"""
        cookie = self.environ.get('HTTP_COOKIE', None)

        if cookie:
            return SimpleCookie(cookie)
        return cookie

    def check_cookie(self, cookie, secret, secret_level=hashlib.sha256):
        return check_cookie(cookie, secret_key=secret, secret_level=secret_level)

    @property
    def method(self):
        return self.environ['REQUEST_METHOD']

    @property
    def query_str(self):
        return self.environ['QUERY_STRING']

    @property
    def parsed_url(self):
        return parse.urlparse(self.url)

    @property
    def query(self):
        """ 返回一个query字典 形式如 {'q': ['a'],...}
            [] 用来指定多次指定相同参数的情况
        """
        return parse.parse_qs(self.query_str)

    @property
    def environ(self):
        """ 返回一个wsgi environ字典的副本 """
        return self.environ.copy()

    @property
    def json(self):
        json_header = self.environ.get('HTTP_CONTENT_TYPE', '').lower()
        if ('application/json' in json_header) or \
            ('application/json-rpc' in json_header):
            try:
                return load(self.body)
            except TypeError as e:
                # TODO: 替换为400错误
                raise e
            except JSONDecodeError as e:
                raise e
        raise AttributeError('Not json body !')

    def _body_iter(self, read, bufsize):
        maxread = max(0, self.content_length)
        while maxread:
            part = read(min(maxread, bufsize))
            if not part:
                break
            yield part
            maxread -= len(part)

    @staticmethod
    def _chunked_iter(read, bufsize):
        err = HttpError(400, "Error while paring chunked transfer body.")
        rn, sem, bs = b'\r\n', b';', b''
        while True:
            header = read(1)
            while header[-2:] != rn:
                c = read(1)
                header += c
                if not c:
                    raise err
                if len(header) > bufsize:
                    raise err
            size, _, _ = header.partition(sem)
            try:
                maxread = int(size.strip().decode(), 16)
            except ValueError:
                raise err
            if maxread == 0:
                break
            buff = bs
            while maxread > 0:
                if not buff:
                    buff = read(min(maxread, bufsize))
                part, buff = buff[:maxread], buff[maxread:]
                if not part:
                    raise err
                yield part
                maxread -= len(part)
            if read(2) != rn:
                raise err

    @property
    def body(self):
        """ 返回一个 BytesIO 对象， 后续访问只seek（0）后返回"""
        try:
            read_func = self.environ['wsgi.input'].read
        except KeyError:
            self.environ['wsgi.input'] = BytesIO()
            return self.environ['wsgi.input']
        body_iter = self._chunked_iter if self.chunked else self._body_iter
        body, body_size, is_temp_file = BytesIO(), 0, False
        for part in body_iter(read_func, self.MEMFILE_MAX):
            body.write(part)
            body_size += len(part)
            if not is_temp_file and body_size > self.MEMFILE_MAX:
                body, tmp = TemporaryFile(mode='w+b'), body
                body.write(tmp.getvalue())
                del tmp
                is_temp_file = True
        self.environ['wsgi.input'] = body
        body.seek(0)
        return body

    @property
    def chunked(self):
        return True if self.environ.get('HTTP_TRANSFER_ENCODING', '') == 'chunked' else False

    @property
    def url(self):
        schema = self.environ['wsgi.url_scheme']
        host = self.environ.get('HTTP_HOST', '')
        path_info = self.environ['PATH_INFO']
        if not host:
            server_name = self.environ['SERVER_NAME']
            server_port = self.environ['SERVER_PORT']
            return ''.join([schema, '://', server_name, ':', server_port, path_info])
        return ''.join([schema, '://', host, path_info])

    @property
    def script_name(self):
        return self.environ['SCRIPT_NAME']

    @property
    def is_xhr(self):
        """ True if the request was triggered by a XMLHttpRequest. This only
            works with JavaScript libraries that support the `X-Requested-With`
            header (most of the popular libraries do). """
        requested_with = self.environ.get('HTTP_X_REQUESTED_WITH', '')
        return requested_with.lower() == 'xmlhttprequest'

    @property
    def is_ajax(self):
        return self.is_xhr

    @property
    def auth(self):
        auth = self.environ.get('HTTP_AUTHORIZATION', '')
        if auth:
            return auth

    @property
    def content_type(self):
        return self.environ.get('CONTENT_TYPE', '')

    @property
    def content_length(self):
        length = self.environ.get('CONTENT_LENGTH', '')
        return int(length) if length else None

    @property
    def form(self):
        """ use cgi fieldstorage 解析 multipart body and return a FileStorage object"""
        if self.method.upper() == 'POST' and \
                (self.content_type.upper().startswith('MULTIPART/') or
                 self.content_type.upper().startswith('APPLICATION/')):
            form = FieldStorage(fp=self.body, environ=self.environ, keep_blank_values=True)
            return form
        else:
            raise AttributeError("Can not parse form data. May form not exists.")

    @property
    def files(self):
        """ from forms parse FileUpload file instance and
         return a dict {filename: FileUpload instance}"""
        try:
            field_list = self.form.list()
        except AttributeError:
            raise

        files = {}
        field_list = field_list or []
        for field in field_list:
            if field.filename:
                files[field.name] = FileUpload(field.file, field.filename,
                                               field.name, field.headers)

        return files

    def get_form_value(self, value, default=None):
        """
        get form value from forms
        :param value: form name
        :param default: if form name field not exists, use this default value to avoid error
        :return: FieldStorage instance or MiniFieldStorage instance with these attrs in f:
        f.name -> field name
        f.filename -> client filesystem filename when upload it
        f.value -> string value
        f.file -> filelike object
        f.type -> content type
        f.type_options -> 在HTTP请求行的内容类型行指定的选项字典
        f.headers -> headers
        see: https://hg.python.org/cpython/file/2.7/Lib/cgi.py
        """
        try:
            return self.form.getvalue(value, default)
        except AttributeError:
            raise

    def get_environ(self, env_item):
        if not isinstance(env_item, str):
            raise AttributeError('{} not exist.'.format(env_item))

        return self.environ.get(env_item)

    @staticmethod
    def parse_range_header(header, maxlen=0):
        """ Yield (start, end) ranges parsed from a HTTP Range header. Skip
            unsatisfiable ranges. The end index is non-inclusive."""
        if not header or header[:6] != 'bytes=': return
        ranges = [r.split('-', 1) for r in header[6:].split(',') if '-' in r]
        for start, end in ranges:
            try:
                if not start:  # bytes=-100    -> last 100 bytes
                    start, end = max(0, maxlen - int(end)), maxlen
                elif not end:  # bytes=100-    -> all but the first 99 bytes
                    start, end = int(start), maxlen
                else:  # bytes=100-200 -> bytes 100-200 (inclusive)
                    start, end = int(start), min(int(end) + 1, maxlen)
                if 0 <= start < end <= maxlen:
                    yield start, end
            except ValueError:
                pass


class RequestWrapper(Request):
    environ = LocalVar()
    init = Request.__init__

