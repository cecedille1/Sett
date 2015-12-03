#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import optparse
from paver.easy import task, cmdopts, consume_nargs

from sett import defaults, __version__ as sett_version


@task
@cmdopts([
    optparse.make_option(
        '--remote',
        default='',
    ),
    optparse.make_option(
        '-m',
        '--method',
        default='POST',
    ),
    optparse.make_option(
        '-s',
        '--stream',
        action='store_true',
        default=False,
    ),
    optparse.make_option(
        '-H',
        '--header',
        action='append',
        dest='headers',
        default=[],
    ),
    optparse.make_option(
        '-q',
        '--ignore-body',
        action='store_true',
        default=False,
    )
])
@consume_nargs(2)
def curl(args, options):
    """Usage: url source"""

    import time
    from sett.utils import optional_import

    requests = optional_import('requests')
    remote = options.remote or 'http://localhost:{}'.format(defaults.HTTP_WSGI_PORT)
    url, source = args

    if url == 'GET' or url == 'HEAD':
        options.method, url, source = url, source, None

    headers = {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'User-Agent': 'sett.curl.curl Sett/{}'.format(sett_version),
    }
    headers.update(h.split(':', 1) for h in options.headers)
    headers.update(defaults.CURL_EXTRA_HEADERS)

    if source == '-':
        data = sys.stdin.read()
    elif source:
        data = open(source, 'rb')
    else:
        data = None

    start = time.time()
    req = requests.request(
        url=remote + url,
        method=options.method,
        headers=headers,
        data=data,
        stream=options.stream,
        allow_redirects=False,
    )
    end = time.time()

    sys.stdout.write('Completion in {}\n'.format(end - start))

    sys.stdout.write('{} {}\n'.format(req.status_code, req.reason))
    for h, v in req.headers.items():
        sys.stdout.write('{}: {}\n'.format(h, v))

    if options.ignore_body:
        return

    if options.stream:
        for line in req.iter_lines():
            sys.stdout.write(line.decode('utf-8'))
    elif req.headers.get('content-type', '').startswith('application/json'):
        import json
        req.encoding = 'utf-8'
        json.dump(req.json(), sys.stdout, indent=4)
    else:
        sys.stdout.write(req.text)
    sys.stdout.write('\n')
