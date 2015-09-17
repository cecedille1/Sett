#!/usr/bin/env python
# -*- coding: utf-8 -*-

import optparse

from paver.easy import path, task, call_task, needs, consume_nargs, info, cmdopts, debug

from sett import ROOT, defaults
from sett.utils import optional_import
from sett.deploy_context import DeployContext

jinja2 = optional_import('jinja2')

DeployContext.register(
    monit={
        'mgroup': 'apps',
        'mmode': 'active',
    },
    options={
        'FORCE_REWRITE': False,
    }
)


@task
@needs(['setup_options'])
@cmdopts([
    optparse.make_option('-r', '--repo',
                         default=defaults.PYPI_REPOSITORY
                         ),
])
def push(options):
    """Pushes the archive in the enix repo"""
    call_task('sdist')
    call_task('upload', options={
        'repository': options.repo,
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
def render_template(args):
    """
    Render a jinja2 template into a file
    """
    template, destination_path = args

    destination_path = ROOT.joinpath(destination_path)
    destination_path.dirname().makedirs()

    template = _get_template(template)
    rendered = template.render(DeployContext())
    info('Writing %s', destination_path)
    with open(destination_path, 'w') as destination:
        destination.write(rendered)


def _get_template(template_name):
    locations = [
        path(__file__).dirname().joinpath('templates'),  # Built in templates
    ]
    if ROOT.joinpath(defaults.DEPLOY_TEMPLATES_DIR):
        locations.append(ROOT.joinpath(defaults.DEPLOY_TEMPLATES_DIR))

    debug('Loading templates from %s', locations)
    jinja = jinja2.Environment(
        loader=jinja2.FileSystemLoader(locations),
    )
    jinja.filters['as_bool'] = lambda x: x if x != 'false' else False
    return jinja.get_template(template_name)
