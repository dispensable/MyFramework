# -*- coding:utf-8 -*-

import hashlib
import itertools
import logging
import mimetypes
import os
import sys
import time
import traceback
from json import dumps
from urllib.parse import quote, urljoin, urlencode

from reloader import reloaders
from .response import ResponseWrapper
from .routin import Route
from .routin import Router
from .utils import CloseIter
from .utils import get_rfc_time, trans_rfc_to_date_time

from myframework.plugin.json_plugin import JsonPlugin
from myframework.request import RequestWrapper
from .error import HttpError, RouteNotFoundException
from .error import InvailideReloader
from .error import UninstallPluginsError
from .error import ReloaderNotExist, ServerAdaptorNotExists
from .plugin.plugin import Plugin
from .plugin.template_plugin import MakoTemplatePlugin, Template
from .server import server_adaptors

request = RequestWrapper()
response = ResponseWrapper()


class MyApp(object):
    """ WSGI app """
    def __init__(self, path, name='default_app'):
        self.root_path = path
        self.config = {}
        self.reload = False
        self.reloader = 'auto'
        self.debug = False
        self.name = name
        self.router = Router()
        self.routes = []

        # {route.callback.__name__: [route]}
        self.func_name_routes = {}

        self.hooks = {'before_request': [],
                      'after_request': [],
                      'before_first_request': [],
                      'app_reset': []}
        self.plugins = []
        self.install(JsonPlugin())
        self.install(MakoTemplatePlugin())
        self.logger = logging.getLogger(__name__)

    def __call__(self, environ, start_response, exe_info=None):
        return self.wsgi(environ, start_response)

    def _init_reloader(self):
        if self.reloader not in reloaders:
            raise InvailideReloader(self.reloader)

        def on_change(fname):
            self.logger.info("Myframework reloading: %s modified", fname)
            time.sleep(0.1)
            sys.exit(0)

        self.reloader = reloaders[self.reloader](callback=on_change)
        self.reloader.start()

    def _load_plugin(self, plugins=None):
        """ load cli plugins """
        plugins = plugins or self.config.get('plugin')
        for plugin in plugins:
            filename, plugin_name = plugin.split(':')
            sys.path.append(os.getcwd())
            try:
                exec('from {} import {}'.format(filename, plugin_name))
            except ImportError:
                raise
            self.install(eval(plugin_name))

    def load_config(self, config):
        self.config = config
        self._override_config()
        self.debug = self.config.get('debug') or False
        self.reload = self.config.get('reload') or False
        if self.reload:
            self.reloader = self.config.get('reloader')
            self._init_reloader()
        self._load_plugin()

    def _override_config(self, config=None):
        param = config or self.config.get('param')
        if param:
            self.config.override_config(param)

    @property
    def debug(self):
        return self.config.get('debug')

    @debug.setter
    def debug(self, value):
        assert isinstance(value, bool), \
            'debug value should be True/False.'
        self.config['debug'] = value

    def wsgi(self, environ, start_response, exe_info=None):
        """ WSGI 入口 """
        try:
            body = self.convert_to_wsgi(self.handle_req(environ))

            if response.status in (100, 101, 204, 304) or \
                            environ['REQUEST_METHOD'] == 'HEAD':
                if hasattr(body, 'close'):
                    body.close()
                body = []

            start_response(response.status_line, response.headers)
            return body
        except (KeyboardInterrupt, SystemExit, MemoryError):
            raise
        except Exception as e:
            errors = traceback.format_exc()
            environ['wsgi.errors'].write(errors)
            environ['wsgi.errors'].flush()

            resp = HttpError(500, 'Internal Server Error',
                             'Error Happened when handle {}'.format(
                                 environ['PATH_INFO']),
                             errors)

            start_response(resp.status_line, resp.headers)
            return [resp.body.encode()]

    def handle_req(self, environ):
        """ 处理请求 """
        # 添加环境变量
        environ['myserver.app'] = self

        # 创建全局request和response变量
        request.init(environ)
        response.init()

        try:
            self.trigger_hook('before_request')
            r_route, args = self.router.match(environ)
            environ['myserver.handle'] = r_route
            environ['myserver.route'] = r_route
            environ['route.url_args'] = args

            if args:
                return r_route.call(**args)
            return r_route.call()
        except RouteNotFoundException:
            return error(404)
        except (KeyboardInterrupt, SystemExit, MemoryError):
            raise
        except Exception as e:
            errors = traceback.format_exc()
            environ['wsgi.errors'].write(errors)
            environ['wsgi.errors'].flush()
            return error(500, 'Internal Server Error', errors)
        finally:
            try:
                self.trigger_hook('after_request')
            except HttpError as e:
                return e

    def convert_to_wsgi(self, respiter):
        """ 将各类返回值转化为wsgi兼容对象
            字典： 转化为json
            空字符串，False, None, None True VALUES: ''
            Unicode字符串（str）： bytes字符串
            HttpError or HttpResponse 对象:
            FilesObject： FileWrapper
            Iterable or Generators： 迭代器对象或者生成器对象，并调用next方法
        """
        # Todo: 编码值使用动态确定 从respiter的header中生成
        print('respiter of convert_to_wsgi: ')
        print(respiter)

        if isinstance(respiter, dict):
            response.content_type = 'application/json'
            try:
                content = dumps(respiter).encode()
            except TypeError:
                raise
            response.content_len = len(content)
            return [content.encode()]

        elif not respiter:
            response.content_len = 0
            return []

        elif isinstance(respiter, (tuple, list)) and \
                isinstance(respiter[0], (str, bytes)):
            respiter = respiter[0][0:0].join(respiter)
            return self.convert_to_wsgi(respiter)

        elif isinstance(respiter, str):
            response.content_len = len(respiter.encode())
            return [respiter.encode()]

        elif isinstance(respiter, bytes):
            response.content_len = len(respiter)
            return [respiter]

        elif isinstance(respiter, HttpError):
            response.status = respiter.status_code
            response.headers = respiter.headers
            return [respiter.body.encode()]

        elif hasattr(respiter, 'read'):
            FileWrapper = request.environ.get('wsgi.file_wrapper')
            return FileWrapper(respiter)

        # iter
        try:
            iter_out = iter(respiter)
            first = next(iter_out)

            while not filter:
                first = next(iter_out)

        except StopIteration:
            return self.convert_to_wsgi('')
        except HttpError as e:
            first = e
        except (KeyboardInterrupt, SystemExit, MemoryError):
            raise
        except Exception as error:
            first = HttpError(500, 'Unhandled exception')

        if isinstance(first, HttpError):
            return self.convert_to_wsgi(first)
        elif isinstance(first, bytes):
            new_respiter = itertools.chain([first], iter_out)
        elif isinstance(first, str):
            new_respiter = map(lambda x: x.encode(response.charset),
                               itertools.chain([first], iter_out))
        else:
            return self.convert_to_wsgi(
                HttpError(500, 'Unsupported iter type: {}'.format(type(first))))
        if hasattr(respiter, 'close'):
            new_respiter = CloseIter(new_respiter, iter_out.close)
        return new_respiter

    def add_hook(self, hookname, func):
        self.hooks[hookname].append(func)

    def remove_hook(self, hookname, func):
        if hookname in self.hooks and func in self.hooks[hookname]:
            self.hooks[hookname].remove(func)

    def trigger_hook(self, hook_name, *args, **kwargs):
        return [hook(*args, **kwargs) for hook in self.hooks[hook_name][:]]

    def hook(self, name):
        def wrapper(func):
            if name in self.hooks:
                self.add_hook(name, func)
            return func
        return wrapper

    def install(self, plugin):
        if not isinstance(plugin, Plugin):
            raise TypeError("Plugin must be a Plugin's subclass.")

        plugin.setup(self)
        self.plugins.append(plugin)
        self.reset()
        return plugin

    def uninstall(self, plugin):
        """ Uninstall plugins.
            if plugin is a instance, remove that instance;
            if plugin is a Plugin class, remove all the instances with this class.
            if plugin is a string , remove the instance with that string name.
            if plugin is True, remove all plugins.
        """
        plugins_list = self.plugins
        results = []

        if isinstance(plugin, Plugin):
            index = plugins_list.index(plugin)
            del plugins_list[index]
            plugin.close()
            return plugin

        elif issubclass(plugin, Plugin):
            for index, plugin_instance in enumerate(plugins_list.copy()):
                if isinstance(plugin_instance, Plugin):
                    this_instance = plugins_list[index]
                    del this_instance
                    this_instance.close()
                    results.append(this_instance)
            return this_instance

        elif isinstance(plugin, str):
            for index, instance in enumerate(plugins_list.copy()):
                if hasattr(instance, 'name'):
                    if instance.name == plugin:
                        this_instance = plugins_list[index]
                        del this_instance
                        this_instance.close()
                        results.append(this_instance)
            return results

        elif plugin is True:
            for index, instance in enumerate(plugins_list.copy()):
                to_del = plugins_list[index]
                del to_del
                to_del.close()
                results.append(to_del)
            return results

        else:
            raise UninstallPluginsError(plugin)

    def reset(self, route=None):
        if route is None:
            routes = self.routes
        elif isinstance(route, Route):
            routes = [route]
        else:
            routes = [r for r in self.routes if r.name == route]

        for route in routes:
            route.reset()

        self.trigger_hook('app_reset')

    def close(self):
        for plugin in self.plugins:
            if hasattr(plugin, 'close'):
                plugin.close()

    def match(self, environ):
        self.router.match(environ)

    def route(self, path=None, method='GET', callback=None,
              name=None, apply=None, skip=None, **config):
        """ 路由装饰器函数
            语法:
            @app.route(path='/hello/<name>')
            def hello_world(name):
                return 'hello world' + str(name)
        """
        def wrapper(func):
            this_route = Route(self, path, method, func, name, apply, skip, **config)

            func_name = func.__name__

            if func_name in self.func_name_routes:
                self.func_name_routes[func_name].append(func_name)
            else:
                self.func_name_routes[func_name] = [this_route]

            self.routes.append(this_route)
            self.router.add_route(this_route)
            return func

        return wrapper

    def get(self, path=None, method='GET', **options):
        """ handy decorator with method get """
        return self.route(path, method, **options)

    def post(self, path=None, method='post', **options):
        """ handy decorator with method post """
        return self.route(path, method, **options)

    def put(self, path=None, method='PUT', **options):
        """ handy decorator with method put """
        return self.route(path, method, **options)

    def delete(self, path=None, method='DELETE', **options):
        """ handy decorator with method delete """
        return self.route(path, method, **options)

    def patch(self, path=None, method='PATCH', **options):
        """ handy decorator with method patch """
        return self.route(path, method, **options)

    def add_filter(self, filter_name, re_rule):
        self.router.add_filter(filter_name, re_rule)

    def render_template(self, *args, **kwargs):
        """ 第一个参数被视为template name, {}视为关键字参数.
            template_plugin: Template Plugin class name
            template_dir:    templates directory (used to find template)

            模板内部的关键字参数全部使用kwargs传入或者在位置参数位置传入dict
        """
        tname = args[0] if args else None

        for dict_arg in args[1:]:
            kwargs.update(dict_arg)

        temp_plugin = kwargs.pop('template_plugin', MakoTemplatePlugin)
        temp_dir = kwargs.pop('template_dir', os.path.join(os.path.dirname(self.root_path), 'templates'))

        return Template(tname, temp_plugin, temp_dir, **kwargs)

    def url_for(self, func_name, **kwargs):
        if func_name in self.func_name_routes:
            encoded_raw_path = quote(self.func_name_routes[func_name][0].raw_path)
            host = request.get_environ('HTTP_HOST')
            scheme = request.get_environ('wsgi.url_scheme')

            base_url = scheme + '://' + host
            encoded_full_url = urljoin(base_url, encoded_raw_path)

            if not kwargs:
                return encoded_full_url
            return encoded_full_url + '?' + urlencode(kwargs)
        else:
            raise RouteNotFoundException(func_name, 'GET')


def error(status_code, phrase=None, traceback=None):
    return HttpError(status_code, phrase=phrase, traceback=traceback)


def abort(status_code, phrase=None):
    return HttpError(status_code, phrase=phrase)


def redirect(new_url):
    """
    redirect request to new ulr.

    :param new_url: url to redirct to
    :return: None

    """
    response.status_code = 303
    response.add_header('Location', new_url, unique=True)


def static_file(filename, root, mimetype=True, download=False, charset='UTF-8', etag=None):
    """
    serve static files.

    @route('/static/<filepath:path>')
    def server_static(filepath):
        return static_file(filepath, root='/path/to/your/static/files')

    :param filename: file's filename
    :param root: file's root path
    :param mimetype: guess mimetype. if string, use as file type, if bool, use mime to guess file type.
    :param download: download to check this file. if is a string,
        use this string as download filename, if true, use original name.
    :param charset: charset
    :param etag: etag for efficient web
    :return: Filelike object
    """

    root = os.path.join(os.path.abspath(root), '')
    filename = os.path.abspath(os.path.join(root, filename.strip('\\/')))

    if not filename.startswith(root):
        return error(404, "Access denied!")
    if not os.path.exists(filename) or os.path.isfile(filename):
        return error(404, "File do not exist.")
    if not os.access(filename, os.R_OK):
        return error(403, "Access denied")

    # 设置文件类型
    if mimetype is True:
        # string
        if isinstance(download, str):
            mimetype, encoding = mimetypes.guess_type(download)
        else:
            mimetype, encoding = mimetypes.guess_type(filename)
        if encoding: response.add_header('Content-Encoding', encoding)

    if mimetype:
        if (mimetype[:5] == 'text/' or mimetype == 'application/javascript') \
                and charset and charset not in mimetype:
            mimetype += '; charset=%s' % charset
        response.add_header('Content-Type', mimetype)

    if download:
        download = os.path.basename(filename if download is True else download)
        response.add_header("Content-Disposition", "attachment; filename='%s'" % download)

    stats = os.stat(filename)
    response.add_header('Content-Length', str(stats.st_size))
    response.add_header('Last-Modified', get_rfc_time(stats.st_mtime))
    response.add_header('Date', get_rfc_time(time.gmtime()))

    if etag is None:
        etag = '%d:%d:%d:%d:%s' % (stats.st_dev, stats.st_ino, stats.st_mtime, stats.st_size, filename)
        etag = hashlib.sha1(bytes(etag)).hexdigest()

    if etag:
        response.add_header('Etag', etag)
        req_etag = request.get_environ('HTTP_IF_NONE_MATCH')
        if req_etag and req_etag == etag:
            response.status_code = 304
            return

    check_modify = request.get_environ('HTTP_IF_MODIFIED_SINCE')
    if check_modify:
        modify_time = trans_rfc_to_date_time(check_modify.split(';')[0].strip())
    if modify_time is not None and modify_time >= stats.st_mtime:
        response.status_code = 304
        return

    body = '' if request.method == 'HEAD' else open(filename, 'rb')

    response.add_header('Accept-Ranges', 'bytes')
    range_header = request.get_environ('HTTP_RANGE')
    if range_header:
        # 处理range请求
        ranges = list(request.parse_range_header(range_header, stats.st_size))
        if not ranges:
            return error(416, "Request range not satisfied.")
        offset, end = ranges[0]
        response.add_header('Content-Range', 'bytes %d-%d/%d' % (offset, end-1, stats.st_size))
        response.add_header('Content-Length', str(end - offset))
        if body:
            body = response.iter_file_range(body, offset, end - offset)
            response.status_code = 206
            return body
    return body


def run(app,
        host='127.0.0.1',
        port=8000,
        server='wsgiref',
        interval=1,
        quiet=False,
        reloader=False,
        plugins=None,
        debug=None,
        config=None,
        **kwargs):
    if reloader:
        r_engine = reloaders.get(reloader)
        if not r_engine:
            raise ReloaderNotExist(reloader)
        r_engine().run()

    if plugins:
        assert isinstance(plugins, list)
        app._load_plugin(plugins=plugins)

    if debug:
        app.debug = debug

    if config:
        assert isinstance(config, dict)
        app._override_config(config=config)

    adaptor = server_adaptors.get(server)

    if adaptor:
        server = adaptor(host=host,
                         port=port,
                         interval=interval,
                         quiet=quiet,
                         **kwargs)
        print(server)
        server.run(app)
    raise ServerAdaptorNotExists(adaptor)
