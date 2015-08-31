#!/usr/bin/env python
# -*- coding: utf-8 -*-

import signal
import os
import time
from xml.etree import ElementTree as ET

from paver.easy import task, sh, needs, consume_nargs, call_task, info, environment

from sett.bin import which
from sett.paths import ROOT, LOGS
from sett.pip import VENV_DIR

UWSGI_PATH = ROOT.joinpath('var')
PIDFILE = UWSGI_PATH.joinpath('uwsgi.pid')
SOCKET = UWSGI_PATH.joinpath('uwsgi.sock')
CONFIG = ROOT.joinpath('parts/uwsgi/uwsgi.xml')


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
@needs([
    'build_context',
])
def uwsgi_xml():
    """
    Generates parts/uwsgi/uwsgi.xml
    """

    context = environment.template_context
    config = {
        'pidfile': PIDFILE,
        'daemonize': LOGS,
        'socket': SOCKET,
        'chmod-socket': '660',
        'processes': '1',
        'chown-socket': '{UID}:{GID}'.format(**context),
        'home': VENV_DIR,
        'pythonpath': ROOT,
        'env': [
            'LANG=fr_FR.UTF-8',
            'LC_ALL=fr_FR.UTF-8',
        ],
    }

    if 'DJANGO_SETTINGS_MODULE' in os.environ:
        call_task('django_settings')
        from django.conf import settings
        # django uses package.module.name and uwsgi uses package.module:name
        module, name = settings.WSGI_APPLICATION.rsplit('.', 1)
        config['env'].append('DJANGO_SETTINGS_MODULE={}'.format(os.environ['DJANGO_SETTINGS_MODULE']))
        config['module'] = '{}:{}'.format(module, name)
    elif hasattr(environment, 'wsgi_module'):
        config['module'] = environment.wsgi_module
    else:
        raise RuntimeError('Set environment.wsgi_module')

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
