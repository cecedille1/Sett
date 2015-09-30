#!/usr/bin/env python
# -*- coding: utf-8 -*-

import signal
import os
import sys
import time
from xml.etree import ElementTree as ET

from paver.easy import task, sh, needs, consume_nargs, call_task, info, path

from sett import which, ROOT, defaults
from sett.paths import LOGS
from sett.pip import VENV_DIR
from sett.deploy_context import DeployContext

UWSGI_PATH = ROOT.joinpath('var')
PIDFILE = UWSGI_PATH.joinpath('uwsgi.pid')
CONFIG = ROOT.joinpath('parts/uwsgi/uwsgi.xml')

DeployContext.register(
    uwsgi={
        'pidfile': PIDFILE,
        'config': CONFIG,
    },
    ctl='{} daemon'.format(path(sys.argv[0]).abspath()),
)


@DeployContext.register
def uwsgi_context():
    if defaults.UWSGI_SOCKET_TYPE == 'unix':
        return {
            'uwsgi': {
                'socket': UWSGI_PATH.joinpath('uwsgi.sock')
            }
        }
    else:
        return {
            'uwsgi': {
                'http': '{}:{}'.format(defaults.HTTP_WSGI_IP, defaults.HTTP_WSGI_PORT),
            }
        }


@task
def log_dir():
    """Ensure that the log directory exists"""
    if not LOGS.exists():
        LOGS.makedirs()


@task
@needs([
    'log_dir',
])
def uwsgi_start():
    """Launch the daemon"""
    sh([
        which.uwsgi,
        CONFIG,
    ])


@task
@consume_nargs(1)
def daemon(args):
    """Control the daemon"""
    command, = args
    if command == 'start':
        call_task('uwsgi_start')
    elif command == 'stop':
        call_task('uwsgi_stop')
    elif command == 'restart':
        call_task('uwsgi_stop')
        call_task('uwsgi_start')


@task
def uwsgi_stop():
    """Slay the daemon"""
    try:
        with open(PIDFILE, 'r') as pid_file:
            pid = int(pid_file.read().strip())
    except IOError:
        info('uwsgi had no PID file')
        return

    try:
        os.kill(pid, signal.SIGKILL)
    except OSError:
        info('uwsgi was not running')
        return

    for x in range(5, 11):
        time.sleep(2 ** x / 500)
        try:
            os.kill(pid, 0)
        except OSError:
            break
    else:
        info('Program %s did not respond to SIGKILL, sending SIGTERM', pid)
        os.kill(pid, signal.SIGTERM)


def Element(tag, text):
    el = ET.Element(tag)
    el.text = text
    return el


@task
def uwsgi_xml():
    """
    Generates parts/uwsgi/uwsgi.xml
    """
    context = DeployContext({
        'uwsgi': {
            'processes': 1,
        },
        'env': [
            'LANG=fr_FR.UTF-8',
            'LC_ALL=fr_FR.UTF-8',
        ],
        'locations': {},
        'directories': {},
    })

    module, name = context['wsgi_application'].rsplit('.', 1)
    config = {
        'module': '{}:{}'.format(module, name),
        'pidfile': PIDFILE,
        'daemonize': LOGS.joinpath('uwsgi.log'),
        'processes': str(context['uwsgi.processes']),
        'home': VENV_DIR,
        'pythonpath': ROOT,
        'env': context['env'],
    }

    if 'uwsgi.socket' in context:
        config.update({
            'socket': context['uwsgi.socket'],
            'chown-socket': '{UID}:{GID}'.format(**context),
            'chmod-socket': '660',
        })
    else:
        config.update({
            'http': context['uwsgi.http'],
        })

    if defaults.STATIC_SERVER == 'uwsgi':
        config['static-map'] = [
            '{}={}'.format(context['locations'][key],
                           context['directories'][key])
            for key in context['locations']
        ]

    root = ET.Element('uwsgi')
    for tag_name, text in config.items():
        if isinstance(text, list):
            for text_ in text:
                root.append(Element(tag_name, text_))
        else:
            root.append(Element(tag_name, text))

    root.append(ET.Element('master'))
    root.append(ET.Element('vacuum'))

    destination_path = CONFIG
    destination_path.dirname().makedirs()
    info('Writing %s', destination_path)
    ET.ElementTree(root).write(destination_path)
