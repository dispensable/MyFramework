# -*- coding:utf-8 -*-

from myframework.myframwork import MyApp, request, response, error, redirect, run
from myframework.utils import check_cookie

import os

wsgi_app = MyApp(__file__)


@wsgi_app.route('/4')
def hello():
    print(request)
    if request.cookie is None:
        response.set_cookie('wang', 'test', secret_key='wang')
    else:
        print('-----')
        print(request.cookie['wang'].value)
        is_passed = check_cookie(request.cookie['wang'].value, 'wang')
        if is_passed:
            print('Cookie check passed!')
        else:
            print('Cookie check failed!')

    return '<h1>hello world!</h1>'


@wsgi_app.route(r'/wiki/<name>')
def test(name):
    response.add_header('Content-Length', '15')
    return 'hello world' + name


@wsgi_app.route(r'/wiki/json')
def json():
    return {'test': 1, 'test2': 2}


@wsgi_app.route(r'/test')
def test1():
    return error(404)

wsgi_app.add_filter('alpha', r'[a-zA-Z]+')


@wsgi_app.route(r'/test/<name:int>/<test:float>/<this:alpha>')
def test2(name, test, this):
    assert isinstance(name, int)
    assert isinstance(test, float)
    return '{}:{}:{}'.format(name, test, this)


@wsgi_app.route(r'/render')
def test3():
    return wsgi_app.render_template('base.html', name='Mako')


@wsgi_app.route(r'/')
def test4():
    return redirect('http://127.0.0.1:8000/4')


@wsgi_app.hook(name='after_request')
def test22():
    print('test after request hook')


@wsgi_app.route(r'/render', method='POST')
def form_test():
    print(request.form.getvalue('beans'))
    response.status_code = 201
    return 'test'


@wsgi_app.route(r'/test_url_for')
def test_url_for():
    return redirect(wsgi_app.url_for('form_test'))

if __name__ == '__main__':
    run(app=wsgi_app, port=8080, server='myserver')
