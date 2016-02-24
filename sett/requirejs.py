#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os
import subprocess

from paver.easy import (task, no_help, consume_args, consume_nargs, call_task,
                        info, needs, path, debug, error, sh)
from paver.deps.six import text_type, string_types

from sett import ROOT, which, defaults, parallel
from sett.utils import Tempdir
from sett.npm import NODE_MODULES


class RJSBuild(object):
    """
    A wrapper arround a r.js command. It takes the requirejs *name* of the
    module to build, the *source* directory, the *out* directory, and a dict of
    *defaults* for the r.js command.

    A list of the file used to build is written in a file name
    ``.*name*.files`` next to the file generated in *out*. This list of files
    is checked by ``should_build`` to avoid regenerating the build file if no
    script have been touched since the last generation.

    **Note**: The file loaded by the plugins are not checked.
    """
    def __init__(self, name, source, out, defaults, cache):
        self.name = name
        self.source = path(source)
        self.out = path(out)
        self.defaults = defaults
        self.cache = cache

    @property
    def config_js(self):
        """
        The path to the config.js file.
        """
        return self.source.joinpath(defaults.RJS_CONFIG)

    def get_command(self, **kw):
        """
        Return the r.js command to invoke. The kwargs is a list of option for
        r.js. Options should be a map of string to strings. They are joined by
        a ``=``.

        >>> self.get_command(preserveLicenseComments='true', name=self.name)
            ['/usr/bin/node.js', '/usr/lib/node_modules/.bin/r.js', '-o',
             'preserveLicenseComments=true', 'name=app/app']
        """
        c = [
            which.node,
            which.search('r.js'),
            '-o',
        ]
        c.extend(map('='.join, kw.items()))
        return c

    def should_build(self):
        return self.cache.is_up_to_date()

    def build(self):
        """
        Invoke the r.js command. It checks the output of the r.js process to
        write the list of files in ``cache_file``.

        If the r.js process returns with anything else than 0, it raises a
        ``RuntimeError``.
        """

        info('Writing %s', self.out)
        command = self.get_command(
            baseUrl=self.source,
            mainConfigFile=self.config_js,
            optimize=defaults.RJS_OPTIMIZE,
            out=self.out,
            **self.defaults
        )
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

        # The config file is not added by requirejs as the list of files
        files.append(self.config_js)
        self.cache.write(files)

    def parse_output(self, stdout):
        """
        Parse the output of the r.js process. It expects a marker printed by
        r.js before the list of files. It raises a ``RuntimeError`` if this
        marker is not encountered else it returns the list of files.
        """
        output = []
        for line in stdout:
            output.append(line.decode('utf-8'))
            if line.startswith(b'-------------'):
                break
        else:
            error('rjs said: %s', '\n'.join(output))
            raise RuntimeError('r.js did not write the expected marker')

        files = []
        for line in stdout:
            # resolve path
            line = line.decode('utf-8').strip()
            if line:
                files.append(line)
        return files


class AlmondRJSBuild(RJSBuild):
    """
    An implementation for a scenario of r.js when a single app handle a page.
    It uses almond.
    """
    def get_almond_path(self):
        """The path to almond"""
        almond = NODE_MODULES.joinpath('almond/almond')
        return self.source.relpathto(almond)

    def get_command(self, **kw):
        kw.update(
            name=kw.pop('almond', None) or self.get_almond_path(),
            include=self.name,
            insertRequire=self.name,
        )
        return super(AppRJSBuild, self).get_command(**kw)


AppRJSBuild = AlmondRJSBuild


class FilesListComparator(object):
    """
    Keeps a file containing a list of path to files.
    """

    def __init__(self, out):
        self.out = out
        self.cache_file = self.out.dirname().joinpath('.{}.files'.format(self.out.basename()))

    def is_up_to_date(self):
        """
        Determines if the module should be built. It should be built if:

        * There is no out file.
        * There is no cache.
        * There is a file in the cache that has been modified since the out
        file have been built.
        """
        try:
            out_build_time = self.out.stat().st_mtime
        except OSError:
            return True

        debug('Read cache from %s', self.cache_file)
        try:
            line = self.cache_file
            dep_write_time = 0
            with open(self.cache_file, 'r') as file:
                for line in file:
                    line = line.strip()
                    if '!' in line:
                        continue
                    dep_write_time = max(dep_write_time, os.stat(line).st_mtime)
        except OSError as e:
            debug('Choked on %s: %s', line, e)
            return True

        debug('out written at %s, max(deps) at %s', out_build_time, dep_write_time)
        # Return should_write = True when the last dependency was written after
        return dep_write_time > out_build_time

    def write(self, files_list):
        """
        Write the cache file
        """
        debug('Writing cache in %s', self.cache_file)
        with open(self.cache_file, 'w') as out_file:
            for file in files_list:
                out_file.write(text_type(path(file).realpath()))
                out_file.write(u'\n')


class RJSBuilder(object):
    """
    A builder for a set of r.js modules.

    >>> rjsb = RJSBuilder(ROOT.joinpath('build/js'))
    """

    def __init__(self, outdir, force=False, build_class=AlmondRJSBuild, defaults=()):
        self.outdir = outdir
        self.force = force
        self.build_class = build_class
        self.defaults = self.get_defaults()
        self.defaults.update(defaults)

    def get_defaults(self):
        """
        Returns a list of default values.
        """
        return {
            'generateSourceMaps': 'true',
            'preserveLicenseComments': 'false',
            'skipDirOptimize': 'false',
            'wrap': 'true',
        }

    def _build(self, rjs_build):
        if self.force or rjs_build.should_build():
            rjs_build.build()

    def autodiscover(self, tempdir, appdir):
        """
        Tries to find under *appdir* in the *tempdir* all the ``js`` files and
        returns the matching requirejs module names.
        """
        args = []
        info('Auto discovering JS %s', appdir)
        appdir = path(appdir)
        for dir in path(tempdir).walkdirs(appdir):
            args.extend(text_type(appdir.joinpath(x.namebase)) for x in dir.files('*.js'))
        debug('Autodicovered: %s', args)
        return args

    def get_builds(self, source, args):
        """
        Returns a list of  ``RJSBuild`` instances for the given modules.
        """
        defaults = dict(self.defaults)
        defaults.pop('appdir', None)

        for name in args:
            out = ROOT.joinpath(self.outdir, name + '.js')
            cache = FilesListComparator(out)
            yield self.build_class(name, source, out, defaults, cache)

    def __call__(self, tempdir, args):
        if not args:
            # Auto discover
            args = self.autodiscover(tempdir, self.defaults.get('appdir', 'app'))
        else:
            debug('Filtered args: %s', args)

        if not args:
            info('No file to optimize')
            return

        build_list = list(self.get_builds(tempdir, args))
        builder = parallel(self._build, n=min(4, len(build_list)))
        builder.for_each(build_list)


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
    force = '--force' in args
    if force:
        args.remove('--force')

    if args and isinstance(args[0], type):
        cls = args.pop(0)
    else:
        cls = RJSBuilder

    outdir = ROOT.joinpath(defaults.RJS_BUILD_DIR)
    outdir.makedirs()

    buidler = cls(
        defaults.RJS_APP_DIR,
        force=force,
        outdir=outdir,
    )

    with Tempdir() as tempdir:
        call_task('virtual_static', args=[tempdir])
        buidler(tempdir.joinpath('js'), args)


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
            'remove': [
                # Remove with and without trailing /
                ROOT.joinpath(defaults.RJS_BUILD_DIR).normpath().parent,
                ROOT.joinpath(defaults.RJS_BUILD_DIR).normpath().parent.joinpath(''),
            ]
        }):
            call_task('django', args=args)


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
