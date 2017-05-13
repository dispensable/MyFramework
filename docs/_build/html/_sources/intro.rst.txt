.. myframework introduction

简介
====

MyFramework 是一个使用Python实现的，简单的web框架。提供了以下特性：

主要功能
========

* 路由功能：
    * 正则表达式驱动的路由匹配功能
    * 自定义路由过滤器

* 模板支持：
    * 使用 `Mako <http://www.makotemplates.org/>`_ 作为默认模板引擎
    * 通过插件可实现自定义模板引擎（或替换为其他模板引擎）

* HTTP请求数据访问支持：
    * 对HTTP请求数据的便捷访问（通过threadlocal实现）
    * form 数据访问（通过CGI模块实现）
    * file uploads支持
    * cookies支持
    * header访问支持

* HTTP响应数据支持
    * 对Response对象的访问和修改
    * sendfile支持（需操作系统和部署服务器支持）
    * WSGI支持

* 测试服务器支持
    * 内置开发服务器（默认为标准库wsgiref server）
    * debug模式

* 插件功能
    * 针对路由的插件支持
    * 简单，方便的插件开发
    * 内置JSON、Mako插件
    * 插件抽象类（继承后覆盖相关方法即可完成开发）

TODO
=====

    * XSS, CSRF防御
    * 常用服务器适配支持
    * debug模式增强
    * HTTP工具增强
    * 常用模板插件
    * 常用数据库插件
    * app stack支持
    * 子应用挂载自持