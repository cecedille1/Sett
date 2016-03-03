#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from xml.etree import ElementTree as ET

from paver.easy import task, info, path, debug
from paver.deps.six import text_type

from sett import which, ROOT, defaults, optional_import
from sett.daemon import Daemon, daemon_task
from sett.paths import LOGS
from sett.pip import VENV_DIR
from sett.deploy_context import DeployContext


yaml = optional_import('yaml')

UWSGI_PATH = ROOT.joinpath('var')

CONFIG_ROOT = ROOT.joinpath('parts/uwsgi/')


@DeployContext.register_default
def uwsgi_context():
    return {
        'uwsgi': {
            'config': get_uwsgi_output().config_path,
        },
        'ctl': '{} daemon'.format(path(sys.argv[0]).abspath()),
    }


@DeployContext.register_default
def uwsgi_context_socket():
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


def Element(tag, text):
    el = ET.Element(tag)
    el.text = text_type(text)
    return el


@task
def uwsgi_conf():
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
        'processes': context['uwsgi.processes'],
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
    ouput_writer = get_uwsgi_output()
    ouput_writer.write(config)


def get_uwsgi_output():
    out = defaults.UWSGI_OUTPUT_FORMAT
    if out is None:
        # Automatic mode
        if yaml:
            out = 'yml'
        else:
            out = 'xml'
        debug('Guessing %s output', out)

    if out == 'yml':
        return YMLOutput(CONFIG_ROOT.joinpath('uwsgi.yml'))
    elif out == 'xml':
        return XMLOutput(CONFIG_ROOT.joinpath('uwsgi.xml'))

    raise NotImplementedError('No format named {}'.format(out))


class WSGIOutput(object):
    @classmethod
    def provider(cls, fn):
        def wrapper(config_path):
            return cls(fn, config_path)
        return wrapper

    def __init__(self, provider, config_path):
        self.provider = provider
        self.config_path = config_path

    def write(self, config):
        self.config_path.dirname().makedirs()
        info('Writing %s', self.config_path)
        self.provider(config, self.config_path)


@WSGIOutput.provider
def YMLOutput(config, output):
    def literal_presenter(dumper, data):
        return dumper.represent_scalar('tag:yaml.org,2002:str', data)
    yaml.add_representer(path, literal_presenter)

    with open(output, 'w') as ostream:
        yaml.dump({'uwsgi': config}, ostream, default_flow_style=False)


@WSGIOutput.provider
def XMLOutput(config, destination_path):
    root = ET.Element('uwsgi')
    for tag_name, text in config.items():
        if isinstance(text, list):
            for text_ in text:
                root.append(Element(tag_name, text_))
        else:
            root.append(Element(tag_name, text))

    root.append(ET.Element('master'))
    root.append(ET.Element('vacuum'))
    ET.ElementTree(root).write(destination_path)


@daemon_task
def daemon():
    try:
        return Daemon(
            [which.uwsgi, get_uwsgi_output().config_path],
            daemonize=lambda pidfile: ['--pidfile', pidfile, '--daemonize', '/dev/null'],
        )
    except which.NotInstalled:
        return None
