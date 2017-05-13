# -*- coding:utf-8 -*-
import os
import sys
from wsgiref import simple_server

from myframework.config.config import Config
from myframework.config.validate import optional_schema


class BaseApp:
    def __init__(self, argv):
        self.argv = argv
        self.cfg = Config(self.argv)

    def chdir(self, path):
        os.chdir(path)
        sys.path.insert(0, path)

    def load_all_config(self):
        # 解析命令行配置
        self.cfg.get_config_from_cli()

        # 读取配置文件
        filename = self.cfg.settings.get('conf')

        if filename and filename != 'default':
            config = self.cfg.get_settings_from_file(filename)
            # 合并cli指定的配置和默认配置
            self.cfg.merge_cli_setting(self.cfg.settings, self.cfg.default_conf)
            # 合并cli指定的配置文件
            self.cfg.merge_cli_setting(config, self.cfg.settings, schema=optional_schema)
            # 覆盖cli指定的配置项（--param 选项）
            if self.cfg.settings.get('param'):
                self.cfg.override_config(self.cfg.settings.get('param'))
        else:
            self.cfg.merge_cli_setting(self.cfg.settings, self.cfg.default_conf)

    def load_app(self):
        cfg = self.cfg

        try:
            path = cfg.get('chdir')
        except AttributeError:
            path = os.getcwd()
        else:
            if not os.path.exists(path):
                path = os.getcwd()

        self.chdir(path)
        package_app = cfg.get('package.module:app')
        package_module, app = package_app.split(':')

        try:
            exec('from {package_module}'
                 ' import {app}'.format(package_module=package_module, app=app))
        except ImportError:
            raise

        return eval(app)

    def run(self):
        self.load_all_config()
        my_framework_app = self.load_app()
        my_framework_app.load_config(self.cfg)
        host_port = self.cfg.get('bind')
        host, port = host_port.split(':')
        server = simple_server.make_server(host, int(port), my_framework_app)
        server.serve_forever()


def run():
    BaseApp(sys.argv).run()

if __name__ == '__main__':
    run()
