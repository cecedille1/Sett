#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess

from paver.easy import (task, no_help, consume_args, consume_nargs, call_task,
                        info, needs, path, environment, debug, sh)

from sett import ROOT, which, defaults, parallel
from sett.utils import Tempdir
from sett.npm import NODE_MODULES


@task
@consume_args
def rjs(args):
    """Usage: rjs APP [APP...]
Compile a requirejs app.

rjs requires npm apps almond and requirejs.
For an app `x`: the url `/STATIC_ROOT/js/x.js` points to a JS file that loads a
bootstrap. It requires `/STATIC_ROOT/js/config.js` and
`/STATIC_ROOT/js/app/x.js`. The rjs optimizer will optimize app/x and write the
output in `OUTPUT/x.js`.

OUTPUT is the value of ``defaults.RJS_BUILD_DIR`` and defaults to
``ROOT/build/static/js/``.

If the django settings have a value STATICFILES_DIRS_DEV, it will be appended
to the STATICFILES_DIRS setting before loading files.
    """
    outdir = ROOT.joinpath(defaults.RJS_BUILD_DIR)
    force = '--force' in args
    if force:
        args.remove('--force')

    @parallel
    def build(rjs_build):
        if force or rjs_build.should_build():
            rjs_build.build()

    with Tempdir() as tempdir:
        source = tempdir.joinpath('js')
        call_task('virtual_static', args=[tempdir])

        if not args:
            # Auto discover
            args = []
            info('Auto discovering JS apps')
            for dir in path(tempdir).walkdirs(defaults.RJS_APP_DIR):
                args.extend(x.namebase for x in dir.files('*.js'))
            debug('Autodicovered: %s', args)

        if not args:
            info('No file to optimize')
            return

        try:
            for name in args:
                out = ROOT.joinpath(outdir, name + '.js')
                build(RJSBuild(defaults.RJS_APP_DIR + '/' + name, source, out))
        finally:
            build.wait()


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


class RJSBuild(object):
    def __init__(self, name, source, out):
        self.name = name
        self.source = path(source)
        self.out = path(out)

    @property
    def config_js(self):
        return self.source.joinpath(defaults.RJS_CONFIG)

    @property
    def almond(self):
        return NODE_MODULES.joinpath('almond/almond')

    def should_build(self):
        ofc = self.out_file_cache()
        debug('Read cache from %s', ofc)
        try:
            out_build_time = self.out.stat().st_mtime
        except OSError:
            return True

        try:
            dep_write_time = os.stat(self.config_js).st_mtime
            with open(ofc, 'r') as file:
                for line in file:
                    if '!' in line:
                        continue
                    dep_write_time = max(dep_write_time, os.stat(line.strip()).st_mtime)
        except OSError as e:
            debug('Choked on %s: %s', line, e)
            return True

        debug('out written at %s, max(deps) at %s', out_build_time, dep_write_time)
        # Return should_write = True when the last dependency was written after
        return dep_write_time > out_build_time

    def out_file_cache(self):
        return self.out.dirname().joinpath('.{}.files'.format(self.out.basename()))

    def build(self):
        info('Writing %s', self.out)
        command = [
            which.node,
            which.search('r.js'),
            '-o',
            'baseUrl={}'.format(self.source),
            'mainConfigFile={}'.format(self.config_js),
            'optimize={}'.format(defaults.RJS_OPTIMIZE),
            'generateSourceMaps=true',
            'preserveLicenseComments=false',
            'skipDirOptimize=false',
            'name={}'.format(self.source.relpathto(self.almond)),
            'include={}'.format(self.name),
            'insertRequire={}'.format(self.name),
            'out={}'.format(self.out),
            'wrap=true',
        ]
        debug('Running: %s', ' '.join(command))
        rjs_process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
        )
        try:
            files = self.parse_output(rjs_process.stdout)
        finally:
            rc = rjs_process.wait()

        if rc != 0:
            raise RuntimeError('r.js returned with {}'.format(rc))
        self.write_cache(files)

    def parse_output(self, stdout):
        for line in stdout:
            debug(line)
            if line.startswith(b'-------------'):
                break
        else:
            raise RuntimeError('r.js did not write the expected marker')

        files = []
        for line in stdout:
            # resolve path
            line = line.decode('utf-8').strip()
            if line:
                files.append(path(line).realpath())
        return files

    def write_cache(self, files):
        out_path = self.out_file_cache()
        debug('Writing cache in %s', out_path)
        with open(out_path, 'w') as out_file:
            for file in files:
                out_file.write(str(file))
                out_file.write('\n')


@task
@consume_args
def madge(args):
    """
    Runs a madge dependency analysis
    """
    with Tempdir() as tempdir:
        call_task('virtual_static', args=[tempdir])
        command = [
            which.madge,
            '-f', 'amd',
            '-R', tempdir.joinpath('js/config.js'),
            tempdir.joinpath('js'),
        ]
        command.extend(args)
        sh(command)


@task
@consume_args
def uglify(args):
    for name in args:
        input = ROOT.joinpath('scripts/js/', name + '.js')
        output = ROOT.joinpath('static/js/', name + '.js')

        sh([
            which.node,
            which.uglifyjs,
            input, '-o', output,
            '--source-map', output + '.map',
            '--source-map-url', name + '.js.map',
            '--compress', '--mangle',
        ])
