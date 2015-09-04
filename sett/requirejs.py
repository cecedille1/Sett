#!/usr/bin/env python
# -*- coding: utf-8 -*-


import tempfile
import subprocess

from paver.easy import (task, no_help, consume_args, consume_nargs, call_task,
                        info, needs, path, environment, debug)

from sett.paths import ROOT
from sett.bin import which
from sett.npm import NODE_MODULES


@task
@consume_args
def rjs(args, options):
    """Usage: rjs APP [APP...]
Compile a requirejs app.

rjs requires npm apps almond and requirejs.
For an app `x`: the url `/STATIC_ROOT/js/x.js` points to a JS file that loads a
bootstrap. It requires `/STATIC_ROOT/js/config.js` and
`/STATIC_ROOT/js/app/x.js`. The rjs optimizer will optimize app/x and write the
output in `OUTPUT/x.js`.

OUTPUT is the value of 'paver.environment.requirejs_output_directory' and
defaults to 'ROOT/build/static/js/'.

If the django settings have a value STATICFILES_DIRS_DEV, it will be appended
to the STATICFILES_DIRS setting before loading files.
    """
    tempdir = path(tempfile.mkdtemp())
    outdir = ROOT.joinpath(getattr(environment, 'requirejs_output_directory', 'build/static/js'))

    try:
        source = tempdir.joinpath('js')
        call_task('virtual_static', args=[tempdir])

        if not args:
            # Auto discover
            args = []
            info('Auto discovering JS apps')
            for dir in path(tempdir).walkdirs('app'):
                args.extend(dir.files('*.js'))
            debug('Autodicovered: %s', args)

        if not args:
            info('No file to optimize')
            return

        for name in args:
            out = ROOT.joinpath(outdir, name + '.js')
            call_task('rjs_build', args=['app/' + name, source, out])
    finally:
        tempdir.rmtree()


@task
@no_help
@needs('django_settings')
@consume_nargs(1)
def virtual_static(args):
    """
    Collect the static in the directory given in argument
    """
    tempdir, = args
    args = ['collectstatic', '--verbosity', '0', '--noinput', '--link']

    from django.conf import settings
    from django.test.utils import override_settings, modify_settings

    with override_settings(STATIC_ROOT=tempdir):
        with modify_settings(STATICFILES_DIRS={
            'append': getattr(settings, 'STATICFILES_DIRS_DEV', []),
        }):
            call_task('django', args=args)


@task
@no_help
@consume_nargs(3)
def rjs_build(args):
    """Do the rjs compilation

Usage: rjs_build `name` `js source directory ` `output`
Example: rjs_build app/index /tmp/static/ /project/static/js/index.js
    """
    name, source, out = args
    source = path(source)
    config_js = source.joinpath('config.js')
    almond = NODE_MODULES.joinpath('almond/almond')

    info('Writing %s', out)

    null = open('/dev/null', 'w')
    rjs_process = subprocess.Popen([
        which.node,
        which.search('r.js'),
        '-o',
        'baseUrl={}'.format(source),
        'mainConfigFile={}'.format(config_js),
        'optimize=uglify2',
        'generateSourceMaps=true',
        'preserveLicenseComments=false',
        'skipDirOptimize=false',
        'name={}'.format(source.relpathto(almond)),
        'include={}'.format(name),
        'insertRequire={}'.format(name),
        'out={}'.format(out),
        'wrap=true',
    ],
        stdout=null,
        stderr=null,
    )
    rjs_process.wait()
    null.close()
