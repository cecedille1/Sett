#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os
import subprocess

from paver.easy import (task, no_help, consume_args, consume_nargs, call_task,
                        info, needs, path, debug, sh)

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
    def __init__(self, name, source, out, defaults):
        self.name = name
        self.source = path(source)
        self.out = path(out)
        self.defaults = defaults

    @property
    def config_js(self):
        """
        The path to the config.js file.
        """
        return self.source.joinpath(defaults.RJS_CONFIG)

    @property
    def cache_file(self):
        """
        The path of the cache file.
        """
        return self.out.dirname().joinpath('.{}.files'.format(self.out.basename()))

    def should_build(self):
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
            dep_write_time = os.stat(self.config_js).st_mtime
            with open(self.cache_file, 'r') as file:
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
        self.write_cache(files)

    def parse_output(self, stdout):
        """
        Parse the output of the r.js process. It expects a marker printed by
        r.js before the list of files. It raises a ``RuntimeError`` if this
        marker is not encountered else it returns the list of files.
        """
        for line in stdout:
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
        """
        Write the cache file
        """
        debug('Writing cache in %s', self.cache_file)
        with open(self.cache_file, 'w') as out_file:
            for file in files:
                out_file.write(str(file))
                out_file.write('\n')


class AppRJSBuild(RJSBuild):
    """
    An implementation for a scenario of r.js when a single app handle a page.
    It uses almond.
    """
    @property
    def almond(self):
        """The path to almond"""
        return NODE_MODULES.joinpath('almond/almond')

    def get_command(self, **kw):
        kw.update(
            name=self.source.relpathto(self.almond),
            include=self.name,
            insertRequire=self.name,
        )
        return super(AppRJSBuild, self).get_command(**kw)


class RJSBuilder(object):
    """
    A builder for a set of r.js modules.

    It takes a the name *appdir* which contains the files to build from the
    static env.

    >>> rjsb = RJSBuilder('app', ROOT.joinpath('build/js'))

    When called it will autodiscover apps or filter the one given in args and
    build them each if necessary (``RJSBuild.should_build``).
    """

    def __init__(self, appdir, outdir, force=False, build_class=AppRJSBuild, defaults=()):
        self.appdir = path(appdir)
        self.outdir = outdir
        self.force = force
        self.build = parallel(self._build)
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

    def autodiscover(self, tempdir):
        """
        Tries to find under *appdir* in the *tempdir* all the ``js`` files and
        returns the matching requirejs module names.
        """
        args = []
        info('Auto discovering JS %s', self.appdir)
        for dir in path(tempdir).walkdirs(self.appdir):
            args.extend(self.appdir.joinpath(x.namebase) for x in dir.files('*.js'))
        debug('Autodicovered: %s', args)
        return args

    def get_builds(self, source, args):
        """
        Returns a list of  ``RJSBuild`` instances for the given modules.
        """
        for name in args:
            out = ROOT.joinpath(self.outdir, name + '.js')
            yield self.build_class(name, source, out, self.defaults)

    def filter(self, args):
        """
        Filters the args to match only those under the *appdir*.
        """
        return [arg for arg in args if arg.startswith(self.appdir)]

    def __call__(self, tempdir, args):
        source = tempdir.joinpath('js')
        if not args:
            # Auto discover
            args = self.autodiscover(tempdir)
        else:
            args = self.filter(args)
            debug('Filtered args: %s', args)

        if not args:
            info('No file to optimize')
            return

        try:
            for build in self.get_builds(source, args):
                self.build(build)
        finally:
            self.build.wait()


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

    buidler = cls(
        defaults.RJS_APP_DIR,
        force=force,
        outdir=ROOT.joinpath(defaults.RJS_BUILD_DIR)
    )

    with Tempdir() as tempdir:
        call_task('virtual_static', args=[tempdir])
        buidler(tempdir, args)


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
