#!/usr/bin/env python
# -*- coding: utf-8 -*-

from paver.easy import path, task, call_task, needs, info, debug, consume_args, error, sh

from sett import ROOT, defaults, which
from sett.utils import optional_import
from sett.utils.dispatch import Dispatcher
from sett.deploy_context import DeployContext

jinja2 = optional_import('jinja2')
_jinja_instance = None


@task
@needs(['wheel'])
def push(options):
    """Pushes the archive in the enix repo"""
    call_task('sdist')
    call_task('upload', options={
        'repository': defaults.PYPI_REPOSITORY,
    })


@task
def etc():
    """
    Make the etc directory with the conf files
    """
    call_task('nginx_conf')
    call_task('monit_conf')
    call_task('uwsgi_conf')


@task
def nginx_conf():
    """
    Generates etc/nginx.conf
    """
    render_template(defaults.NGINX_TEMPLATE, 'etc/nginx.conf', {
        'options': {
            'FORCE_REWRITE': False,
        }
    })


@task
@needs('setup_options')
@consume_args
def systemd(args, options):
    sdd = SystemdDispatcher(
        options.setup.name,
    )
    for arg in args:
        sdd(arg)


class SystemdDispatcher(Dispatcher):
    def __init__(self, name, local_service_path=None, system_service_path=None):
        self.name = name
        self._local_service_path = local_service_path
        self._system_service_path = system_service_path

    @property
    def local_service_path(self):
        return self._local_service_path or ROOT.joinpath('etc/systemd.service')

    @property
    def system_service_path(self):
        return (self._system_service_path or
                path('/etc/systemd/system/').joinpath('{}.service'.format(self.name)))

    def _systemd(self, *args):
        sh([which.systemctl] + list(args))

    def _reload(self):
        self._systemd('daemon-reload')

    @Dispatcher.on('restart', 2)
    @Dispatcher.on('up', 2)
    def start(self):
        """Start the service"""
        self._systemd('start', self.name)

    @Dispatcher.on('restart', 1)
    def stop(self):
        """Stop the service"""
        self._systemd('stop', self.name)

    @Dispatcher.on('install', 1)
    @Dispatcher.on('up', 1)
    def link(self):
        """Creates a link in the system"""
        try:
            self.local_service_path.symlink(self.system_service_path)
        except OSError:
            error('Cannot write %s, sudo maybe?', self.system_service_path)
            info('# ln -s {target} {link}'.format(
                target=self.local_service_path,
                link=self.system_service_path,
            ))
        else:
            self._reload()

    @Dispatcher.on('uninstall', 1)
    def unlink(self):
        print('unlink')
        self._reload()

    @Dispatcher.on('install', 2)
    @Dispatcher.on('up', 3)
    def enable(self):
        self._systemd('enable', self.name)

    @Dispatcher.on('uninstall', 2)
    def disable(self):
        self._systemd('disable', self.name)


@task
def systemd_conf():
    """
    Generates etc/systemd.conf
    """
    render_template(defaults.SYSTEMD_TEMPLATE, 'etc/systemd.service', {
        'systemd': {
            'KillSignal': None,
        }
    })


@task
def monit_conf():
    """
    Generates etc/monit.conf
    """
    render_template(defaults.MONIT_TEMPLATE, 'etc/monit.conf', {
        'monit': {
            'mgroup': 'apps',
            'mmode': 'active',
        },
    })


def render_template(template, destination_path, context=tuple()):
    """
    Render a jinja2 template into a file
    """
    destination_path = ROOT.joinpath(destination_path)
    destination_path.dirname().makedirs()

    template = _get_template(template)
    rendered = template.render(DeployContext(context))
    info('Writing %s', destination_path)
    with open(destination_path, 'w') as destination:
        destination.write(rendered)


def _get_template(template_name):
    global _jinja_instance
    if _jinja_instance is None:
        _jinja_instance = make_jinja_instance()
    return _jinja_instance.get_template(template_name)


def make_jinja_instance():
    debug('Creating jinja instance')
    location = path(__file__).dirname().joinpath('templates')
    debug('Loading builtin templates from %s', location)
    loader = jinja2.FileSystemLoader(location)  # Built in templates

    if ROOT.joinpath(defaults.DEPLOY_TEMPLATES_DIR):
        location = ROOT.joinpath(defaults.DEPLOY_TEMPLATES_DIR)
        debug('Loading templates from %s', location)
        # Load users or builtin
        loader = jinja2.ChoiceLoader([
            jinja2.FileSystemLoader(location),
            loader,
            jinja2.PrefixLoader({
                'super': loader,
            })
        ])

    jinja = jinja2.Environment(loader=loader)
    jinja.filters['as_bool'] = lambda x: x if x != 'false' else False
    return jinja
