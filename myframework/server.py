# -*- coding:utf-8 -*-


class ServerAdaptor:
    def __init__(self, host='127.0.0.1', port=8080, **kwargs):
        self.host = host
        self.port = int(port)
        self.options = kwargs

    def run(self, app):
        pass

    def __str__(self):
        return "Server adaptor: {} running at {}:{!s}".format(
            self.__class__.__name__, self.host, self.port)

    def __repr__(self):
        return 'Server adator: {!s}' \
               ' with options\n {!s}'.format(
                self.__class__.__name__,
                self.options
                )


class WsgirefServerAdaptor(ServerAdaptor):
    def run(self, app):
        from wsgiref.simple_server import make_server
        from wsgiref.validate import validator

        server = make_server(self.host, self.port, validator(app))
        server.serve_forever()


class MyServerAdaptor(ServerAdaptor):
    def run(self, app):
        try:
            from myserver.app.baseapp import App
        except ImportError:
            raise

        class MyownApp(App):
            def load(self):
                return app

        myapp = MyownApp()
        myapp.run()


server_adaptors = {
    'wsgiref': WsgirefServerAdaptor,
    'myserver': MyServerAdaptor
}