.. use

概览
====

快速起步
-------

让我们先从一个最简单的`hello world`示例开始讲起吧。

.. code-block:: python

    from myframwork import MyApp

    # 建立应用
    myapp = MyApp(__file__)

    # 定义路由
    @myapp.route(r'/')
    def hello():
        return 'hello world!'

首先导入框架中的MyApp类，实例化之后就得到一个

请求路由
--------

静态路由
^^^^^^^

动态路由
^^^^^^^^

HTTP METHOD
^^^^^^^^^^^^

静态文件
^^^^^^^^

错误处理
^^^^^^^^

路由返回值
----------

dict: {}
^^^^^^^^^

'', True/False, None, anything is not True
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

string: str or bytes
^^^^^^^^^^^^^^^^^^^^

HTTP Error object
^^^^^^^^^^^^^^^^^

迭代器和生成器
^^^^^^^^^^^^

改变charset
^^^^^^^^^^^

静态文件
^^^^^^^

重定向和HTTP 错误码
^^^^^^^^^^^^^^^^^

Responsable object
^^^^^^^^^^^^^^^^^^^

status code
^^^^^^^^^^^^

响应头部
^^^^^^^

cookies
^^^^^^^

* cookie

* signed cookie

HTTP 工具
---------

cookies
^^^^^^^

headers
^^^^^^^

query variables
^^^^^^^^^^^^^^^

form data
^^^^^^^^^

file uploads
^^^^^^^^^^^^

JSON data
^^^^^^^^^

Request body
^^^^^^^^^^^^

WSGI variables
^^^^^^^^^^^^^^

模板
====

默认模板：mako
^^^^^^^^^^^^^

模板插件
^^^^^^^

自定义模板引擎
^^^^^^^^^^^^

开发工具
====

debug
-----

reloader
--------

command line interface
----------------------

部署
----
