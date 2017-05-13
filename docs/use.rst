.. use

开发概览
====

快速起步
----

让我们先从一个最简单的`hello world`示例开始讲起吧。

.. code-block:: python

    from myframwork import MyApp, run

    # 建立应用
    myapp = MyApp(__file__)

    # 定义路由
    @myapp.route(r'/')
    def hello():
        return 'hello world!'

    if __name__ == '__main__':
        run(app=myapp, host='127.0.0.1', port=8080)

运行该程序：

.. code-block:: shell
    $ python3 myapp.py
    Server adaptor: WSGIrefAdaptor running at 127.0.0.1:8080

打开浏览器，在地址栏输入 http://127.0.0.1:8080 就可以看到熟悉的`hello world`了。
让我们逐行解释下到底发生了什么。

首先我们导入MyApp类，这是我们要定义的web应用的类，实例化之后得到一个MyApp实例。run函数使用
一系列参数决定运行时服务器的设置。

然后我们实例化该类，传入参数为app所在的目录，__file__总是指向我们定义app的模组目录，所以大多
情况下，直接使用__file__即可灵活的定义app目录，避免写死在程序里。

接着我们调用app实例myapp的一个实例方法，返回一个装饰器函数，这个函数接受一系列的参数，其中最
重要的就是路径参数，该参数决定了http请求时的请求路径对应的函数。这里我们指定/主目录对应下面
定义的hello函数——也就是说在访问/路径时，将触发hello函数的运行，并返回相应结果。

然后是熟悉的 `if __name__ == '__main__:'`,指定模组直接执行时的行为，我们的调用导入的run
函数来启动一个服务器，run函数也接受一系列的参数来定义运行时的行为，这里我们传入app实例，和需要
绑定的端口位置。一个简单的`hello world`程序就完成了。

我们运行程序，之后在浏览器点击`http://127.0.0.1:8080`时，浏览器向服务器发出一个http GET请求，
服务器通过WSGI
将该请求的处理发送给web框架，web框架在对请求做适当的包装和处理之后，构建起request对象并在所有
的路由中找寻匹配的路径（此处为`\\`），查找到相关路由之后，调用该路由指定的处理函数（此处为返回
`hello world`字符串。）web
框架在收到函数的返回值之后，将其加工成WSGI兼容的数据格式，添加相关的头部和http响应数据，构建HTTP
response 对象，之后将该对象的相关值返回到服务器，服务器将该结果发送到浏览器，浏览器识别和处理
HTTP 响应之后，显示我们响应的内容。

这就是全部的处理过程了。

请求路由
--------

路由配置是一组指令，用来告诉router 如何匹配URL以及匹配后如何执行代码。在上一节中我们写了一个简单
的路由函数:

.. code-block:: python

   @myapp.route(r'/')
   def hello():
       return 'hello world'

route装饰器的作用，就是讲请求路径和需要执行的代码关联起来，route装饰器接收一个path参数，讲用户定义的hello
函数添加到myapp的路由列表中。在需要匹配路径时，通过Router类完成路由的匹配与执行。

可以在路由路径中添加过滤器，完成对某些特殊路由的匹配工作：

.. code-block:: python

    @myapp.route(r'/<name>')
    def hello():
        # some handle code
        return 'hello world {name!s}'.format(name=name)

上述代码将匹配路径中的<name>部分，并将其赋值给name变量，你可以在处理函数中引用该变量。过滤器还有很多更灵活的
应用，详见 :ref:`filter-label`。以下详解说明路由的编写。

静态路由
^^^^

静态路由非常简单，直接在route装饰器中指明路径和方法即可,还可以通过 `name` 参数指定路由的名称。我们重点来谈论
下动态路由。

.. _filter-label:

动态路由
^^^^

在路径参数中包含通配符的路由被称之为动态路由。因为通配符的原因，它可以匹配多条符合通配符的路径，简单的通配符示例
如 `@myapp.route('/wiki/<name>')` 将变量名包裹在<>尖括号中。在匹配成功之后，即可在回调函数中引用该变量。方
括号以为着此处可以匹配多个不同长度的字符，但是包含 `\/` 的内容匹配将会失败。例如，`/wiki/test` 匹配成功，`/wiki
/testtesttest` 也会成功，但是 `/wikitest/test` 不会成功， `/wiki/test/test` 也不会成功。

你也可以在路径中指定过滤器，用来处理更加特殊的路径模式。使用 `<name:filter_name>` 来使用内置过滤器，使用
`<name:fileter_name:config>` 来使用自定义的过滤器和re过滤器。通过config指定需要传入的参数。

MyFramework已经内置了以下四种过滤器：

* :int 匹配整数并将其转化为整数
* :float 匹配浮点数并将该值转为浮点数
* :path 匹配路径（例如托管的静态文件 `r'/static/<path:path>'`
* :re 使用Python正则表达式过滤路径，匹配成功的路径不会被替换。

示例:

.. code-block:: python

    @myapp.route(r'/testint/<name:int>')
    def callback(name):
        assert isinstance(name, int)

    @myapp.route(r'/testfloat/<name:float>')
    def callback(name):
        assert isinstance(name, float)

    @myapp.route(r'/testre/<name:re:[a-zA-Z]+>')
    def callback(name):
        assert name.isalpha()

    @myapp.route(r'/static/<path:path>')
    def callback(path):
        return static_file(path, ...)

你还可以实现自定义的filter，使用myapp的实例方法 `add_filter(filter_name, re_rules):` 即可添加新的
filter。第一个参数指定filter的name（在<var_name:filtername>中使用），第二个参数是re正则表达式。

.. code-block:: python

    myapp.add_filter('myfilter', r'[a-zA-Z0-9_]')

上述代码就可以添加一个filter，之后就可以在接下来的代码中使用了。

.. note::
    使用filter时，不要在 `:` 附近加空格，将导致路由无法匹配。（PEP也不建议在参数位置加空格）

HTTP METHOD
^^^^^^^^^^^^

你可以通过route装饰器的method参数指定回调函数的请求方法。除此之外， `myapp` 实例还定义了很多便捷的类方法，
使用这些类方法可以快速指定需要的HTTP request method。列表如下：

* get
* post
* put
* delete
* patch

使用示例：

.. code-block:: python

    from myframwork.myframework import request

    @myapp.get(r'/login')
    def login():
        return """
            <form action="/login" method="post">
                Username: <input name="username" type="text" />
                Password: <input name="password", type="password">
                <input value="Login" type="submit" />
            </form>
        """

    @myapp.post(r'/login')
    def check_login():
        username = request.get_form_value('username', None)
        password = request.get_form_value('password', None)

        if username:
            username = username.value
        if password:
            password = password.value

        # check login here
        if is_log_success(username, password):
            return "<p> login success </p>"
        else:
            return "<p>login failed!</p>"


.. _static_file_label:

静态文件
^^^^

MyFramework支持静态文件托管，你可以将常用的css等文件调用此方法发送，若服务器支持sendfile系统调用，将提高
托管静态文件的性能（或直接配置服务器发送静态文件）。此外，static_file还支持range，if_modified_since等
提高文件传输性能的HTTP HEADER，因此使用静态文件可以获得较高的性能（而不是直接生成bytes数据）。以下是一个
简单的静态文件发送示例：

.. code-block:: python

    from myframework.myframework import static_file

    @myapp.route(r'/static/<path:path>')
    def send_static_file(path):
        return static_file(path, root="/path/to/your/staitc/file")

虽然你可以使用相对路径指明path的根目录，但是注意project的目录和 `./` 不一定时刻都相同。

`static_file` 函数还有很多其他参数：

.. code-block:: python

    static_file(filename, root, mimetype=True, download=False, charset='UTF-8', etag=None):

* filename： 指明请求中静态文件的路径
* root： 指明静态文件的根目录
* mimetype：当mimetype为True时，使用mimetype模块猜测文件类型，当指定文件类型（字符串）时，使用指定的
    文件类型，之后添加到响应header的content-type首部中。
* download： 当为True时，需要下载才能查看该文件，并使用系统文件名作为文件名，当为string时，指定下载的
    文件名为该值。False时，浏览器会直接解析某些文件格式并在浏览器中打开。
* charset： Content-Type首部中的编码
* etag： 指定etag首部的内容，默认为None，使用该文件的Inode所在的设备，Inode编号，最后一次修改的时间、
    文件大小和filename的bytes哈希摘要作为Etag。

.. _error_handle_label:

错误处理
^^^^

当请求的路径不存在相关路由时，MyFramework将直接提供一个404 NotFound页面。你也可以自定义该页面的内容，
使用error，abort，HttpError完成上述任务。简单示例如下：

.. code-block:: python

    from myframwork.myframwork import error, abort
    from myframwork.error import HttpError

    # 使用error
    @myapp.route(r'/wiki/error')
    def error_handle():
        return error(404, 'this page is missing, please check your url.')

    # 使用abort
    @myapp.route(r'/wiki/error2')
    def error2_handle():
        return abort(404, 'there are not no place for no hero.')

    # 使用HttpError
    @myapp.route(r'/wiki/error3')
    def error3_handle():
        return HttpError(500, 'ops, this is all i find.')

事实上，error和abort函数只是对HttpError类的一个简单的包装，error函数包含状态码，短语，traceback三个参数，
abort只包含前两个参数。HttpError初始化参数在error参数的基础上加了一个body参数，用来替换默认的body内容（
状态码短语和trancback的文本展示）

.. note::

    * MyFramework只有在本节使用的函数和类实例中使用错误处理，单独改变response对象的状态码并不会引发错误处理
    * 可以自定义HttpError对象，只要保证它继承自HttpError即可（status_code, body, phrase必须保留）

路由返回值
-----

自定义的路由函数可以返回多种数据类型，MyFramework可以将这些数据类型转换为相应的wsgi兼容对象（各式各样的bytes
对象），下面实现详细的转换规则。

dict: {}
^^^^^^^^

字典会被默认转化为JSON类型，使用标准库中的JSON模块完成转换。同时将在response对象中添加响应的Content-Type
内容。

'', True/False, None, anything is not True
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

以上的所有值都会导致在Response对象中添加Content-Length首部并将其值设置为0。

string: str or bytes
^^^^^^^^^^^^^^^^^^^^

所有的Python字符串对象都将被转化为bytes对象，Unicode字符串将根据request可以接受的编码编码为bytes对象。
并添加响应的Content-Type和Content-Length头部。

HttpError object
^^^^^^^^^^^^^^^^

返回该对象将引发错误处理，并替换响应的statuscode和header内容。


File对象
^^^^^^

如果返回的对象有.read()方法，则被视为File对象，将使用wsgi.file_wrapper进行包装并返回到WSGI服务器
服务器可能会对文件的发送进行优化（使用sendfile等系统调用），从而提高文件发送的性能。

.. note::

    可以直接返回文件对象，但是建议使用static_file，因为它提供了很多提高文件发送性能的优化，
    详见 :ref:`static_file_label`

迭代器和生成器
^^^^^^^

你还可以返回迭代器和生成器，只要返回或者生成的类型是上述数据类型即可。MyFramework会首先生成一个非空的值
来确定数据类型，在处理后生成一个新的迭代器或者生成器回送到WSGI server。

.. Note::

    根据WSGI规范，在生成第一个非空值之前就会发送header，之后对header的修改是无效的。

改变charset
^^^^^^^^^

MyFramework使用Response对象中的charset属性决定如何编码Unicode字符串（默认使用utf-8）编码。因此你可以设置
相关属性完成编码的设置。Content-Type可以使用response.content_type属性改变。

.. code-block:: python

    from myframework.myframewor import response

    @myapp.route('/charset/<charset>')
    def get_charset(charset):
        response.charset = charset
        return "sending with {} encoding".format(charset)

.. note::

    content-type用来发送到客户端，charset用来制定unicode字符串编码。当python的编码名称和RFC不符时，可以
    利用该属性，先设置content-type然后使用charset设置指定python使用的编码方案。

重定向和HTTP错误码
^^^^^^^^^^^

你可以使用redirect函数完成重定向工作，该函数将设置response的状态码和相关首部，下面是一个简单的示例：

.. code-block:: python

    from myframwork.myframwork import redirect

    @myapp.rout(r'/redirect')
    def test_redirect():
        return redirect('http://your/new/url')

在代码中写入硬编码url显然不是个灵活的选择，MyFramework提供了url_for函数生成路由相关的url。

.. code-block:: python

    @myapp.route(r'/route', name='route_name')
    def test_url_for():
        return 'some code you want'

    @myapp.route(r'/redirect')
    def test_redirect():
        return redirect(myapp.url_for('test_url_for'))

.. note::

    使用url_for的理由：

        * url_for 函数将为你自动处理URL编码和/缺失问题；
        * url_for 更加灵活，在修改路由函数路径信息时会一起更新

Responsable object
^^^^^^^^^^^^^^^^^^

所有响应内容的元数据都存储在 `Response` 对象中。线程局部的全局response变量可以用来引用和修改response的
相关属性。也可以使用已经提供了的函数和方法完成。

status code
^^^^^^^^^^^

使用 `response.status` 属性可以直接修改响应对象的状态码，直接赋值整数状态码即可。该属性将自动生成标准的响应
短语。默认值为 `200 OK`（意味着你可能很少需要手动操作该属性）

你也可以使用 :ref:`error_handle_label` 来自定义需要的状态短语

响应头部
^^^^

Response对象提供了一个 `add_header` 方法完成对header的添加和替换。该方法原型如下：

.. code-block:: python

    def add_header(self, header, value, unique=False):
        ...

header参数为需要添加的首部字段，value为其值，若unique指定为True，则将替换已经存在的同名header。

类似的，你可以通过 `get_header(header)` 方法获取header值，也可以通过 `del_header(header)` 方法删除
header。

.. _cookie_label:

cookies
^^^^^^^

Response对象也提供了对cookie的支持。使用Response对象的 `set_cookie(name, value ...)` 方法设置需要的
cookie值。内部是用了python的simplecookie完成cookie的生成。参见
`Simplecookie <https://docs.python.org/3/library/http.cookies.html>`_

set_cookie 函数的参数和默认值如下：

* name: cookie名称
* value: cookie值
* path: (例如 '/', '/mydir') 如果没有定义，默认为当前文档位置的路径。
* domain: (例如 'example.com'， '.example.com' (包括所有子域名), 'subdomain.example.com') 如果没有定义，默认为当前文档位置的路径的域名部分。
* max-age: max-age-in-seconds (例如一年为60*60*24*365)
* expires: date-in-GMTString-format 如果没有定义，cookie会在对话结束时过期
    这个值的格式参见Date.toUTCString()
* secure (cookie只通过https协议传输)
* version: 指定cookie的版本
* httponly: True/False HttpOnly 属性限制了 cookie 对 HTTP 请求的作用范围。特别的，该属性指示用户代理
    忽略那些通过"非 HTTP" 方式对 cookie 的访问（比如浏览器暴露给js的接口）。
    注意 HttpOnly 属性和 Secure 属性相互独立：一个 cookie 既可以是 HttpOnly 的也可以有 Secure 属性。
* header: 默认值：'Set-Cookie'，自定义首部
* secret_key: cookie签名
* secret_level: 签名使用的算法，默认是hashlib.sha256

通过Request对象提供的 `cookie` 属性（返回simplecookie实例）， `get_cookie(cookie_name)` 方法（返回
具体该名称的cookie值）， `check_cookie(...)`方法（完成cookie的验证），完成对cookie的操作。

该方法还支持其他具体的cookie属性设置，具体参见API文档。以下是两个简单的示例。

* 添加cookie

    .. code-block:: python

        from myframework.myframework import request, response

        # 获取cookie
        name_cookie = request.get_cookie('cookie_name')

        # 获取simplecookie实例
        sc_instance = request.cookie

        # 设置cookie
        response.set_cookie('name', 'value')

    .. note::

        * Cookie的大小限制在4KB左右。超出该限制将无法完成cookie设置。
        * 若没有设置cookie，则 `request.cookie` 将抛出CookieNotExist错误，`request.get_cookie()`失败时也会抛出该错误，并指明用户指定的cookie名称。

* signed cookie

    因为cookie保存在客户端，所以其安全性难以把控。签名cookie可以用来对cookie进行签名，生成值和摘要，通过
    服务器秘钥的检验即可保证cookie不被篡改。MyFramework通过标准库的http.cookie和hashlib模块支持cookie
    的签名和验证。在 `response.set_cookie` 参数中使用 `secret_key='your secret_key'`
    和 `secret_key` （默认值为hashlib.sha256) 即可实现签名cookie。 `request.check_cookie`方法实现
    了对签名cookie的验证。

    .. code-block:: python

        from myframwork.utils import check_cookie
        @myapp.route('/check_cookie')
        def check_cookie():
            if request.cookie is None:
                response.set_cookie('cookie_name', 'value', secret_key='secret')
                return 'hello world!'
            else:
                is_passed = check_cookie(request.cookie['cookie_name'].value, 'secret')
                if is_passed:
                    return 'cookie check passed, hello friend'
                else:
                    return 'cookie check not pass, who are you?'

    .. danger::

        ⚠️ 签名cookie仅仅对cookie进行了摘要，并没有对cookie进行加密，在cookie上承载敏感信息总是有巨大风险
        的。

HTTP 工具
-------

MyFramework 为HTTP请求数据进行了进一步的封装，提供一系列工具来访问相关信息。request和response作为全局
变量完成了对HTTP请求和响应数据的封装。通过thead_local变量实现了对多线程访问的支持。因此这两个变量名都是
本次请求的特定的request和response。

cookies
^^^^^^^

Cookie的访问参见 :ref:`cookie_label`

headers
^^^^^^^

* 通过 `request.headers` 属性访问request对象的所有header，headers以字典形式给出（对wsgi
    环境变量的一个包装）
* 通过 `response.get_header(headername)` `response.add_header(header, value, unique=False)`
    `response.del_header(header_name)` 完成响应对象的首部的添加删除和获取。

query variables
^^^^^^^^^^^^^^^

通过 `request.query` 属性可以获取一个查询字符串的字典，形如 {'query': ['value', ...] ...}。采用列表
来保证多个相同名称的值可以得以保存。查询字符串已经完成了url解码。

通过 `request.query_str` 属性可以获取一个查询字符串的python字符串表示，且已经完成url解码。

form data
^^^^^^^^^

通过 `request.form` 属性可以获取一个cgi FieldStorage 实例，其中包含了已经解析后的form属性。若不存在
form则将抛出 `AttributeError` 错误。

通过 `request.get_form_value(value, default=None)` 可以获取相关form的值，其中defalut参数指明了不存在
该参数时返回的默认值。

FieldStorage实例的具体使用请参考Python标准库：
`FieldStorge <https://docs.python.org/3/library/cgi.html>`_

file uploads
^^^^^^^^^^^^

通过 `request.files` 属性可以获取一个字典，形式如 {filename: FileUpload instance ...}. FileUpload
类对form上传的文件进行了包装。添加了 `filename` 和 `save` 方法，若存在header可以通过 `get_header` 获取
对应的name值。

* get_header(name, defualt=None): 获取form的header信息
* filename：返回filename
* save(destination, overwrite=False, chunk_size=2**16): destination为保存路径， overwrite指定在
路径已经存在的情况下，是否覆盖同名文件。chunk_size指定复制文件时的块大小。

JSON data
^^^^^^^^^

使用 `request.json` 方法，获得解码之后的json数据（使用标准库的json解码成Python字典）

Request body
^^^^^^^^^^^^

通过 `request.body` 方法访问body数据。返回值为一个BytesIO对象，其文件指针指向文件头部。

WSGI variables
^^^^^^^^^^^^^^

通过 `request.environ` 属性返回一个 WSGI environment 字典。通过 `request.get_environ(item)`返回特定值。


模板
====

MyFramework使用模板引擎简化html的编写。默认的模板引擎为 `Mako <http://www.makotemplates.org/>`_ 。通过
app实例的render_template方法可以返回模板文件并自定渲染和编码返回文件。

.. code-block:: python

    @myapp.route(r'/test_template')
    def test_template():
        return myapp.render_template('base.html', name='Mako',
            render_post=myapp.url_for('test_post'))


在项目主文件夹下新建一个文件夹命名为template，然后新建一个base.html文件。写入以下内容：

.. code-block:: html

    <h1>hello</h1>
        ${name}
    <br>

    <a href="http://www.dispensable.biz">my website</a>

    <form action="${rend_post}" method="post">
        <p>
            choose your beans:
            <select name="beans">
                <option value="House Blend">House blend</option>
                <option value="Bolivia">Bolivia</option>
            </select>
        </p>

        <p>
            Name: <input type="text" name="name" value=""><br>
        </p>

        <p>
            <input type="submit" value="submit">
        </p>
    </form>


模板设置
----

通过指定 `render_template` tempalte_plugin 参数，可以替换模板引擎，默认为MakoTemplatePlugin。通过
`template_dir` 参数可以指定模板文件的位置。其余关键字参数都会原封不动的传入Template类通过template插件
传入相应的模板引擎。


模板插件
----

框架内置Mako模板插件，通过插件完成模板渲染的功能。插件的开发和模板替换详见 :ref:`plugin-selfdef-label` 。


开发工具
====

MyFramework内置了几个工具方便web开发，主要有：

debug
-----

debug模式下，app中发生的错误会直接抛出，方便调试和开发。通过在run()函数中指定debug参数为True，或者在命令行
界面中指定 `--debug` 选项亦可开启。

reloader
--------

作用： 在配置文件或者代码修改之后自动重启服务器。

通过命令行或者run()函数中指定reloader参数启用，reloader参数为False时不启用，'auto'自动选择reloder引擎，
'inotify'选择linux特有的inotify调用，'poll'使用传统的线程模式完成重启。

command line interface
----------------------

Usage:
^^^^^^

  myframework [options] [-C <KEY=VALUE>...] [-p <PLUGIN>...] <package.module:app>

Options:
^^^^^^^^

+-------------------------------+---------------------------------------------------------+--------------------------+
|  CLI OPTION                   |  Instruction                                            |  Default value           |
+===============================+=========================================================+==========================+
|  -h, --help                   |  show this help message and exit                        |  None                    |
+-------------------------------+---------------------------------------------------------+--------------------------+
|  --version                    |  show version number.                                   |  None                    |
+-------------------------------+---------------------------------------------------------+--------------------------+
|  -b ADDRESS --bind=ADDRESS    |  bind socket to ADDRESS.                                |  127.0.0.1:8080          |
+-------------------------------+---------------------------------------------------------+--------------------------+
|  -s SERVER --server=SERVER    |  use SERVER as backend.                                 |  myserver                |
+-------------------------------+---------------------------------------------------------+--------------------------+
|  -p <PLUGINMODULE:PLUGINNAME> |                                                         |                          |
|  --plugin=<PLUGINMODULE:      |  install additional plugin/s.                           |  None                    |
|           PLUGINNAME>         |                                                         |                          |
+-------------------------------+---------------------------------------------------------+--------------------------+
|  -c FILE --conf=FILE          |  load config values from FILE.                          |  default                 |
+-------------------------------+---------------------------------------------------------+--------------------------+
|  -C <NAME=VALUE>              |  override config values.                                |  None                    |
|  --param=<NAME=VALUE>         |                                                         |                          |
+-------------------------------+---------------------------------------------------------+--------------------------+
|  --debug                      |  start server in debug mode.                            |  False                   |
+-------------------------------+---------------------------------------------------------+--------------------------+
|  --reload                     |  auto-reload on file changes.                           |  False                   |
+-------------------------------+---------------------------------------------------------+--------------------------+
|  --reloader RELOADER          |  choose reloader (auto, poll, inotify).                 |  auto                    |
+-------------------------------+---------------------------------------------------------+--------------------------+

部署
----

run()函数
^^^^^^^


通过run()函数可以快速的使用内置的测试服务器，方便开发。run函数有很多参数，说明之前首先看一个示例：

.. code-block:: python

    from myframework.myframework import run
    # all the app code

    if __name__ == "__main__":
        run(app=myapp, port=8080, server='wsgiref')

直接运行该模组，就可以看到启动的效果了。

run函数的参数列表如下：

.. code-block:: python

    def run(app,
        host='127.0.0.1',
        port=8000,
        server='wsgiref',
        interval=1,
        quiet=False,
        reloader=False,
        plugins=None,
        debug=None,
        config=None,
        **kwargs):

* app: 指定app示例
* host： 指定服务器绑定的IP地址
* port： 指定服务器绑定的端口
* server： 指定server adaptor，默认使用wsgiref服务器（Python的wsgi参考服务器）框架还内置了'myserver'适配器，
    其他适配器正在开发中，你也可以根据api自定义服务器适配器，从而启用自己的开发服务器。
* interval： 轮询时间
* quiet： 是否输出错误
* reloader： 重载引擎
* plugins: 要启用的插件，若指定，应为列表
* debug： 是否开启debug模式
* config： 需要为覆盖的框架配置
* kwargs： 其余关键字参数，原封不动的传入到server适配器中。

ServerAdaptor 自定义
--------------------

你可以为自己需要使用的服务器自定义适配器，继承ServerAdaptor类，然后实现其run()方法即可。
run方法接受一个app实例作为其参数。ServerAdaptor的初始化参数为run函数的参数列表。参见 :ref:`run-label`

一个简单的的示例如下：

.. code-block:: python

    from myframework.server import ServerAdaptor

    class WsigirefServerAdaptor(ServerAdaptor):
        def run(self, app):
            from wsgiref.simpleserver import make_server
            from wsgiref.validate import validator

            server = make_server(self.host, self.port, validator(app))
            server.server_forever()

