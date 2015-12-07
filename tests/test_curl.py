# -*- coding: utf-8 -*-

import sys

try:
    from unittest import mock
except ImportError:
    import mock

from sett.curl import curl
from paver.tasks import environment
from paver.easy import Bunch


def test_curl_get():
    environment.options = Bunch(
        remote='',
        headers=[],
        method='POST',
        stream=False,
        ignore_body=False,
    )
    environment.args = ['GET', '/api/v1/']
    requests = mock.Mock()

    response = requests.request.return_value = mock.Mock()
    response.headers = {
        'content-type': 'text/plain',
    }

    with mock.patch.multiple('sett.curl',
                             requests=requests,
                             defaults=mock.Mock(
                                 HTTP_WSGI_PORT=9000,
                                 HTTP_WSGI_IP='192.168.1.1',
                                 CURL_EXTRA_HEADERS=[],
                             ),
                             sett_version='test',
                             create=True):
        curl()

    requests.request.assert_called_once_with(
        url='http://192.168.1.1:9000/api/v1/',
        method='GET',
        headers={
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'sett.curl.curl Sett/test',
        },
        data=None,
        stream=False,
        allow_redirects=False,
    )


def test_curl_post():
    Open = mock.Mock()
    requests = mock.Mock()

    environment.options = Bunch(
        remote='',
        headers=[],
        method='POST',
        stream=False,
        ignore_body=False,
    )
    environment.args = ['/api/v1/', 'file.json']

    response = requests.request.return_value = mock.Mock()
    response.status = 200
    response.reason = 'OK'
    response.headers = {
        'content-type': 'application/json',
    }
    response.json.return_value = {'a': 'b'}
    json = mock.Mock()

    with mock.patch.multiple('sett.curl',
                             requests=requests,
                             open=Open,
                             defaults=mock.Mock(
                                 HTTP_WSGI_PORT=9000,
                                 HTTP_WSGI_IP='192.168.1.1',
                                 CURL_EXTRA_HEADERS=[],
                             ),
                             json=json,
                             sett_version='test',
                             create=True):
        curl()

    Open.assert_called_once_with('file.json', 'rb')
    requests.request.assert_called_once_with(
        url='http://192.168.1.1:9000/api/v1/',
        method='POST',
        headers={
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'sett.curl.curl Sett/test',
        },
        data=Open.return_value,
        stream=False,
        allow_redirects=False,
    )
    json.dump.assert_called_once_with({'a': 'b'}, sys.stdout, indent=4)
