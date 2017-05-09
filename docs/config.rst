.. config

框架配置选项
===========

从命令行配置
-----------

运行myframework -h 可以查看所有帮助信息，使用相关选项可覆盖默认配置。各配置选项介绍见从配置文件配置

.. code-block:: shell

    $ myframework -h


从配置文件配置
-------------

使用以下命令指定配置文件

.. code-block:: shell

   $ myserver -c <configfile>

配置文件为普通的python文件，你可以在`/MyFramework/myframework/config/default_conf.py`查看所有可配置项。
配置文件应该是一个python模组。具体可配置选项如下：

bind
^^^^

    默认值: '127.0.0.1:8080'

    可选值: ipv4地址

    说明: 指定web服务器绑定的端口

    示例:

.. code-block:: python

   bind = '127.0.0.1:8080'

conf
^^^^

    默认值: 'default'

    可选值: 配置文件目录

    说明: default表示使用默认配置

    示例:

.. code-block:: python

   conf = 'default'

debug
^^^^^

    默认值: False

    可选值: True/False

    说明: 是否启用debug模式（更多的错误输出）

    示例:

.. code-block:: python

   debug = False

param
^^^^^

    默认值: {}

    可选值: 字典（在使用命令行时，使用键值对列表 `name=value name=value ...`

    说明: 需要覆盖的配置选项

    示例:

.. code-block:: python

   param = {'name': value}

plugin
^^^^^^

    默认值: []

    可选值: 需要启用的插件

    说明: 根据列表中指示的插件模组和模组名称载入模组（默认在全局启用）

    示例:

.. code-block:: python

   plugin = ['plugin_module:plugin_name'...]

reload
^^^^^^

    默认值: False

    可选值: True/False

    说明: 是否启用自动重载

    示例:

.. code-block:: python

   reload = False

server
^^^^^^

    默认值: 'wsgiref'

    可选值: server adaptor 名称（默认为wsgiref服务器）

    说明: 此配置选项用来选择托管的服务器

    示例:

.. code-block:: python

   server = 'myserver'

version
^^^^^^^

    默认值: False

    可选值: True/False

    说明: 显示版本号

reloader
^^^^^^^^

    默认值: 'auto'

    可选值: 'inotify'/'poll'

    说明: reloader引擎的名称（需要系统平台支持）auto自动选择reloader（若支持inotify则启用inotify）

    示例:

.. code-block:: python

   reloader = 'auto'

