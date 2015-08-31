#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import getpass
import os
import grp

from paver.easy import path, task, call_task, needs, consume_nargs, info, no_help, environment

from sett import uwsgi
from sett.paths import ROOT
from sett.utils import optional_import

jinja2 = optional_import('jinja2')

templates_dir = path(__file__).dirname().joinpath('templates')


@task
@no_help
@needs(['setup_options'])
def build_context():
    name = environment.options.setup.name.lower()
    context = {
        'uwsgi': {
            'pidfile': uwsgi.PIDFILE,
            'socket': uwsgi.SOCKET,
            'config': uwsgi.CONFIG,
        },
        'ctl': '{} daemon'.format(path(sys.argv[0]).abspath()),
        'domain': 'dev.{}.emencia.net'.format(name),
        'monit': {
            'mgroup': 'apps',
            'mmode': 'active',
        },
        'ROOT': ROOT,
        'NAME': name,
        'UID': getpass.getuser(),
        'GID': grp.getgrgid(os.getgid()).gr_name,
        'options': {
            'FORCE_REWRITE': False,
        }
    }
    environment.template_context = context


@task
@needs(['setup_options'])
def push():
    """Pushes the archive in the enix repo"""
    call_task('sdist')
    call_task('upload', options={
        'repository': 'http://enixpi.enix.org',
    })


@task
def etc():
    """
    Make the etc directory with the conf files
    """
    call_task('nginx_conf')
    call_task('monit_conf')
    call_task('uwsgi_xml')


@task
def nginx_conf():
    """
    Generates etc/nginx.conf
    """
    call_task('render_template', args=['nginx.conf.jinja', 'etc/nginx.conf'])


@task
def monit_conf():
    """
    Generates etc/monit.conf
    """
    call_task('render_template', args=['monit.conf.jinja', 'etc/monit.conf'])


@task
@consume_nargs(2)
@needs(['build_context'])
def render_template(args):
    """
    Render a jinja2 template into a file
    """
    template, destination_path = args

    destination_path = ROOT.joinpath(destination_path)
    destination_path.dirname().makedirs()

    template = _get_template(template)
    rendered = template.render(environment.template_context)
    info('Writing %s', destination_path)
    with open(destination_path, 'w') as destination:
        destination.write(rendered)


def _get_template(template_name):
    jinja = jinja2.Environment(
        loader=jinja2.FileSystemLoader([
            ROOT.joinpath('templates'),
            templates_dir,
        ]),
    )
    jinja.filters['as_bool'] = lambda x: x if x != 'false' else False
    return jinja.get_template(template_name)
