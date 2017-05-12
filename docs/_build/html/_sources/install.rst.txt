.. install and run

安装 & 运行
===========

从源码安装
---------

下载源码后直接使用Python setuptools完成安装，成功后运行-h可查看帮助

.. code-block:: shell

    $ git clone https://github.com/dispensable/MyFramwork.git
    $ python3 setup.py install
    $ myframework -h
    $ myframework <pakage>.<module>:<app>

或者直接下载源码后运行`/myframework/main.py -h`亦可

.. note::

    确保package目录在当前目录下

    `demo`文件夹的`wsgiapp.py`中存放了一个简单的示例。


