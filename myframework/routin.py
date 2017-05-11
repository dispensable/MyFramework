# -*- coding:utf-8 -*-
import re

from myframework.error import RouteNotFoundException, RouteReset
from myframework.error import UnknownFilterException
from .utils import FilterDict, CachedProperty

PATTERN = re.compile(r'<(.*?)>')


class Router(object):
    def __init__(self):
        self.routes = []

    def add_route(self, route):
        if not isinstance(route, Route):
            raise TypeError('{} must be a Route instance'.format(route))
        self.routes.append(route)
        self.routes.sort(key=lambda route: route.path)
        self.routes.reverse()

    def url_for(self, router):
        return router.path

    def match(self, environ):
        env_path = environ.get('PATH_INFO', '/')
        method = environ.get('REQUEST_METHOD', 'GET')
        # 匹配出router
        for route in self.routes:
            # 匹配方法
            if route.method != method:
                continue

            # 静态路由匹配
            if route.is_static:
                if route.path == env_path:
                    return route, {}
                continue

            # 动态路由匹配
            is_match = re.match(route.path, env_path)
            if is_match:
                return route, is_match.groupdict()
        raise RouteNotFoundException(env_path, method)

    def add_filter(self, filter_name, re_rule):
        """ Add a new filter to the route class.
            name: filter name (str)
            re: filter discard (use re)
        """
        Route.filter_pattern[filter_name] = r'(?P<{name}>%s)' % re_rule


class Route(object):

    filter_pattern = FilterDict()

    def __init__(self, app, path, method, callback, name, apply_list, skip, **config):
        self.app = app
        self.path = path
        self.method = method
        self.callback = callback
        self.name = name or None
        self.plugin_list = apply_list or []
        self.skip = skip or []
        self.config = config
        self.trans_to_re()

    @CachedProperty
    def call(self):
        callback = self.callback
        try:
            for plugin in self.all_plugins:
                callback = plugin.apply(callback, self)
        except RouteReset:
            del self.__dict__['call']
            return self.call()
        return callback

    @property
    def all_plugins(self):
        unique = set()
        for p in reversed(self.app.plugins + self.plugin_list):
            if True in self.skip:
                break
            name = getattr(p, 'name', False)

            # skip plugins we don't need
            if name and (name in self.skip or name in unique):
                continue
            if p in self.skip or type(p) in self.skip:
                continue
            if name:
                unique.add(name)
            yield p

    def reset(self):
        self.__dict__.pop('call', None)

    @property
    def is_static(self):
        return '<' not in self.path

    @property
    def is_with_filter(self):
        return ('<' in self.path) and (':' in self.path)

    @staticmethod
    def _find_filters(path):
        """ from path find all filters and name or re rules and add them to a list
            :return [(name, filter [, re_rules])...]
        """
        name_and_filter_list = re.findall(r'<([^/]+)>', path)
        orgin_name = []

        for name_and_filter in name_and_filter_list:
            name, filter_name, *rest = name_and_filter.split(':')
            orgin_name.append((name, filter_name, ''.join(rest))
                              if rest else (name, filter_name))

        return orgin_name

    def trans_to_re(self):
        """ transfer all filter into a re filter """
        # 静态路由不转换
        if self.is_static:
            return

        # 动态无过滤器
        elif not self.is_with_filter:
            self.path = self._regular_to_re(self.path)

        # 动态有过滤器
        else:
            self.path = self._filter_to_re(self.path)

    def _regular_to_re(self, path):
        # find all names
        all_names = re.findall(r'<([^/]+)>', path)
        # 替换为普通过滤器
        regular = self.filter_pattern['regular']
        for name in all_names:
            path = path.replace('<{}>'.format(name), regular.format(name=name))

        return path

    def _filter_to_re(self, path):
        # find all names and filters
        name_filters = self._find_filters(path)
        # 替换为相关的路由
        for name, f, *rule in name_filters:
            # 构造新的re
            if f == 're':
                re_rule = r'(?P<{name}>{rule})'.format(name=name, rule=rule[0])
            else:
                r = self.filter_pattern.get(f)
                if f:
                    re_rule = r.format(name=name)
                else:
                    raise UnknownFilterException(f)

            old_re = '<{name}:{f}>'.format(name=name, f=f) \
                if not rule else '<{name}:{f}:{rule}>'.format(name=name, f=f, rule=rule[0])
            # 替换为新re
            path = path.replace(old_re, re_rule)
        return path

    def __str__(self):
        return '<Route for path: {}>'.format(self.path)