from myframework.utils import _HTTP_STATUS_LINES


class MyFramworkException(Exception):
    pass


class InvailideReloader(MyFramworkException):
    def __init__(self, reloader_name):
        self.reloader = reloader_name

    def __str__(self):
        return 'Invalide reloader: {}'.format(self.reloader)


class HeaderNotAllowed(MyFramworkException):
    def __init__(self, header, code):
        self.header = header
        self.code = code

    def __str__(self):
        return "{!s} not allwoed in {!s} status code".format(self.header, self.code)


class PluginError(MyFramworkException):
    pass


class PluginAlreadyExistsException(PluginError):
    def __init__(self, plugin, msg=None):
        self.plugin = plugin
        self.msg = msg

    def __str__(self):
        return self.msg or "{plugin} already exists.".format(plugin=self.plugin)


class UninstallPluginsError(PluginError):
    def __init__(self, plugin):
        self.plugin = plugin

    def __str__(self):
        return 'Unexcepted plugin argv: {!s}'.format(self.plugin)


class RouteException(MyFramworkException):
    pass


class RouteNotFoundException(RouteException):
    def __init__(self, path, method):
        self.path = path
        self.method = method

    def __str__(self):
        return "{} {} didn't match any route.".format(self.method, self.path)


class RouteReset(RouteException):
    def __init__(self, route):
        self.route = route

    def __str__(self):
        return "Route {!s} has been reseted.".format(self.route)


class UnknownFilterException(RouteException):
    def __init__(self, filter_name):
        self.filter = filter_name

    def __str__(self):
        return 'Unknown filter {}, try to add it?'.format(self.filter)


class CookieException(MyFramworkException):
    pass


class CookieAuthError(CookieException):
    def __init__(self, cookie):
        self.cookie = cookie

    def __str__(self):
        return "Cookie {} not authenticated! ".format(self.cookie)


class CookieNotExist(CookieException):
    def __init__(self, cookie_name, msg=None):
        self.cookie_name = cookie_name
        self.msg = msg

    def __str__(self):
        return self.msg if self.msg else "Cookie {} not exist!".format(self.cookie_name)


class HttpError(Exception):
    def __init__(self, status_code, phrase=None, body=None, traceback=None):
        self.status_code = status_code
        self.phrase = phrase or _HTTP_STATUS_LINES.get(status_code)
        self.body = body or """
                <h1>HTTP ERROR : {!s}</h1>
                <p>REASON: {!s}</p>
                <p>see <a href="http://127.0.0.1:8000">here for detail</a></p>
                <p>--------- traceback --------</p>
                {traceback}
                """.format(self.status_code, self.phrase, traceback=traceback)
        self.headers = [('Content-Type', 'text/html; charset=UTF-8'),
                        ('Content-Length', str(len(self.body)))]
        self.status_line = str(self.status_code) + self.phrase

    def __str__(self):
        return self.body


class ReloaderNotExist(MyFramworkException):
    def __init__(self, reloader_name, msg=None):
        self.name = reloader_name
        self.msg = msg

    def __str__(self):
        return "Reloader {} not exist.".format(self.name) if not self.msg else self.msg


class ServerAdaptorNotExists(MyFramworkException):
    def __init__(self, adaptor_name, msg=None):
        self.name = adaptor_name
        self.msg = msg

    def __str__(self):
        return "Server adaptor {} not exists.".format(self.name) if not self.msg else self.msg