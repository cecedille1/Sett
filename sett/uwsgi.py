#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from xml.etree import ElementTree as ET

from paver.easy import task, info, path

from sett import which, ROOT, defaults
from sett.daemon import Daemon, daemon_task
from sett.paths import LOGS
from sett.pip import VENV_DIR
from sett.deploy_context import DeployContext

UWSGI_PATH = ROOT.joinpath('var')
CONFIG = ROOT.joinpath('parts/uwsgi/uwsgi.xml')

DeployContext.register(
    uwsgi={
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


@daemon_task
def daemon():
    try:
        return Daemon(
            [which.uwsgi, CONFIG],
            daemonize=lambda pidfile: ['--pidfile', pidfile, '--daemonize', '/dev/null'],
        )
    except which.NotInstalled:
        return None


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
        'env': [],
        'locations': {},
        'directories': {},
        'pythonpath': ROOT,
    })

    module, name = context['wsgi_application'].rsplit('.', 1)
    config = {
        'module': '{}:{}'.format(module, name),
        'logto': LOGS.joinpath('uwsgi.log'),
        'processes': str(context['uwsgi.processes']),
        'home': VENV_DIR,
        'env': context['env'],
        'pythonpath': context['pythonpath'],
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

    config.update(defaults.UWSGI_EXTRA)

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
