from docopt import docopt
from myframework import __version__

CLI_DOC = """Myframwork.
Usage:
  myframework [options] [-C <KEY=VALUE>...] [-p <PLUGIN>...] <package.module:app>

Options:
  -h, --help            show this help message and exit
  --version             show version number.
  -b ADDRESS --bind=ADDRESS
                        bind socket to ADDRESS. [default: 127.0.0.1:8080]
  -s SERVER --server=SERVER
                        use SERVER as backend. [default: myserver]
  -p <PLUGINMODULE:PLUGINNAME> --plugin=<PLUGINMODULE:PLUGINNAME>
                        install additional plugin/s.
  -c FILE --conf=FILE   load config values from FILE. [default: default]
  -C <NAME=VALUE> --param=<NAME=VALUE>
                        override config values.
  --debug               start server in debug mode. [default: False]
  --reload              auto-reload on file changes. [default: False]
  --reloader RELOADER   choose reloader (auto, poll, inotify). [default: auto]"""


if __name__ == '__main__':
    arguments = docopt(CLI_DOC, version=__version__)
    print(arguments)
