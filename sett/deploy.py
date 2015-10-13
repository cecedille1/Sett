#!/usr/bin/env python
# -*- coding: utf-8 -*-

from paver.easy import path, task, call_task, needs, info, debug

from sett import ROOT, defaults
from sett.utils import optional_import
from sett.deploy_context import DeployContext

jinja2 = optional_import('jinja2')
_jinja_instance = None


@task
@needs(['setup_options'])
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
    call_task('uwsgi_xml')


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
