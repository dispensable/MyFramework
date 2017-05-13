.. plugin install and dev

插件
====

MyFramework只实现了核心的web框架功能，如果需要更丰富的功能，可以通过他的插件系统进行自定义，也可以安装第三方
的插件实现更加丰富的功能。

内置插件
----

框架自定义了两个基础的插件：

* json_plugin（将Python字典输出为JSON内容）
* MakoTemplatePlugin（识别Mako模板对象并自动渲染）

插件安装和卸载
-------

使用 `myapp.install(plugin_class())` 即可完成插件的安装，并自动触发路由的重置功能。框架将调用插件实例的setup()
方法。若需要卸载插件，使用 `myapp.uninstall(plugin)` 卸载插件，若参数plugin为插件类的实例，则移除该实例；若为
插件类，则移除该插件类的所有实例；若为字符串，则移除name属性为该字符串的所有插件；若为True，则移除所有插件。所有以上
行为都会导致相关路由函数的重置。

**插件的安装顺序和应用顺序相反**，先安装的插件最后才会被应用到路由函数上。你也可以通过路由函数装饰器的applylist指定该路由函数
特有的插件，可以通过skiplist跳过某些指定插件的使用，这些被跳过的插件将不会影响到此路由。

若卸载失败，则抛出UninstallPluginError，并指出plugin参数的名称。

插件API
-----

参见 :ref:`plugin-api-label` .

.. _plugin-selfdef-label:

自定义插件
-----

所谓插件，本质上就是对用户定义的路由函数的一个包裹函数。插件本身虽然以类的形式存在，但本质上是一个装饰器。在需要对路由函数
操作时，插入相关代码，并返回新的函数作为路由函数。在不需要任何操作时，直接返回原来的回调函数即可。

通过继承和实现Plugin类的相关方法，可以很方便的完成插件的开发。下面以模板插件为例，讲解插件的开发：

.. code-block:: python

    class TemplatePlugin(Plugin):
        def __init__(self, name, template_dir=os.getcwd()+'/templates', api_version=0.1):
            self.template_dir = template_dir
            super(TemplatePlugin, self).__init__(name, api_version)

        def setup(self, app):
            """ called when install plugin to the app
                :param app: Myframwork instance
             """
            for p in app.plugins.copy():
                if isinstance(p, TemplatePlugin) and p.template_dir == self.template_dir:
                    raise PluginAlreadyExistsException(self)

        def __call__(self, callback, route):
            """ Been called to apply directly to each route callback. """
            raise NotImplementedError

        def apply(self, callback, route):
            raise NotImplementedError

        def close(self):
            """ been called when uninstall this plugin """
            raise NotImplementedError

    class MakoTemplatePlugin(TemplatePlugin):
        def __init__(self):
            from mako.lookup import TemplateLookup
            self.TemplateLookup = TemplateLookup
            super(MakoTemplatePlugin, self).__init__('MaKo Template Plugin', api_version=0.1)

        def __call__(self, callback, route):
            self.apply(callback, route)

        def apply(self, callback, route):
            config = route.config

            @wraps(callback)
            def wrapper(*args, **kwargs):
                result = callback(*args, **kwargs)
                if isinstance(result, Template):
                    lookup = self.TemplateLookup(directories=result.dir, **config)
                    mytemplate = lookup.get_template(result.temp_name)
                    return mytemplate.render(**result.kwargs)
                return callback(*args, **kwargs)
            return wrapper

        def close(self):
            pass


为了方便模板类的开发，框架从Plugin继承了一个Plugin类，称之为TemplatePlugin类。原Plugin类要求必须有name和api_version
两个参数。

.. note::

    所有的插件都必须继承自Plugin类，并实现该抽象类指定的抽象方法。所有抽象方法参见： :ref:`plugin-api-label`

* name： 插件的名称（也可以用来对插件进行卸载）
* api_version: 目前只有0.1版

Template类添加了template_dir作为模板的搜索目录。

在setup方法中，我们接受了一个app实例作为参数，此处可以自定义安装时的细节和需要进行的准备工作。完成后直接在app.plugins属性
中添加插件实例即可，此处我们检查了是否有和我们共用template目录的template实例，如果有就放弃安装，并抛出PluginAlreadyExsitsException

在__call__方法中，我们接受一个callback函数——即用户定义的路由函数和对应的route对象。当插件类直接被调用时，会直接使用本处
的代码。此处我们直接代理到了apply方法。

在apply方法中，我们接受和__call__相同的方法参数。你可以通过对路由函数和route对象的操作完成相应的插件功能，插件应该被实现
成一个装饰器，接受路由回调函数和路由对象本身。若不需要任何动作，请直接返回回调函数，若需要执行任何代码，在包裹回调函数之后
请返回经过包裹的包裹函数，借而完成插件功能。

route实例参数提供了该路由的特定上下文信息，其属性和方法列表参见 :ref:`routin-label` 。利用route的上下文信息，可以方便的
定义插件需要的参数值。所有在route装饰器中传入的关键字参数，都会保存在route实例对象的相关属性中。

在close方法中，若插件有需要进行清理的部分，所有插件在被卸载时都会调用其close方法，若没有需要进行的清理动作，可以直接
使用pass略过该方法的执行。若需要执行清理工作，请添加响应代码（如关闭文件描述符，关闭数据库连接，关闭网络连接等）。仔细研究
上述代码示例，应该可以非常轻松的完成相关插件的开发。