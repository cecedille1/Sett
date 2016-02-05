# -*- coding: utf-8 -*-

import os.path
import collections
import importlib

from sett import optional_import, defaults, ROOT
from paver.easy import task, info, debug, consume_args, call_task
from paver.deps.six import string_types

observers = optional_import('watchdog.observers')
events = optional_import('watchdog.events')
libsass = optional_import('sass', 'libsass')


@task
@consume_args
def sass(args):
    """
    Usage: sass [compile|watch]

    Shortcut to sassc_watch and sassc_compile.
    """
    if not args:
        command = 'compile'
    else:
        command = args[0]

    if command == 'compile':
        call_task('sassc_compile')
    elif command == 'watch':
        call_task('sassc_watch')
    else:
        raise ValueError('Usage: sass [compile|watch]')


@task
def sassc_compile(ROOT):
    """Compile the sass files"""
    s = Sass.default()
    debug('Building with %s', s)
    s()


@task
def sassc_watch():
    """Watch the filesystem for modifications and run sass if needed"""
    s = Sass.default()
    debug('Building/watching with %s', s)
    s()

    import time
    try:
        with Watcher(s):
            info('Starting watch %s', s)
            while True:
                time.sleep(10)
    except KeyboardInterrupt:
        pass


class EventDispatcher(object):
    """Watchdog compatible event dispatcher. It calls the builder when a file
    is modified and have the right extension"""
    def __init__(self, builder):
        self.builder = builder
        self.extensions = {'.css', '.scss'}

    def dispatch(self, event):
        #  events.FileCreatedEvent triggers FileModifiedEvent
        if isinstance(event, (events.FileModifiedEvent)) and event.src_path in self:
            self.builder(event.src_path)

    def __contains__(self, path):
        stem, ext = os.path.splitext(path)
        if ext not in self.extensions:
            return False
        if os.path.basename(stem).startswith('_'):
            return False
        return True


class Watcher(object):
    """Watchdog compatible event dispatcher"""
    def __init__(self, builder):
        self.observer = observers.Observer()

        self.watches = {}
        for path in builder.paths:
            watch = self.observer.schedule(EventDispatcher(builder), path, recursive=True)
            self.watches[path] = watch

    def __enter__(self):
        self.observer.start()

    def __exit__(self, exc_value, exc_type, traceback):
        self.observer.stop()
        self.observer.join()


class BaseSass(object):
    @classmethod
    def get_default_paths(self):
        sp = defaults.SASS_PATH
        if isinstance(sp, string_types):
            return sp.split(':')
        if isinstance(sp, collections.Iterable):
            return [ROOT.joinpath(d) for d in sp]

        bc = ROOT.joinpath('bower_components/'),
        if bc.isdir():
            return [bc]
        return []

    @classmethod
    def get_default_functions(self):
        functions = []
        functions_names = ([defaults.SASS_FUNCTIONS]
                           if isinstance(defaults.SASS_FUNCTIONS, string_types) else
                           defaults.SASS_FUNCTIONS)

        for sassf in functions_names:
            if isinstance(sassf, string_types):
                module = importlib.import_module(sassf)
                functions.extend(f for f in vars(module).values() if isinstance(f, libsass.SassFunction))
            elif isinstance(sassf, libsass.SassFunction):
                functions.append(sassf)
            else:
                raise TypeError('unexpected %s in defaults.SASS_FUNCTIONS' % sassf)

        return functions

    @classmethod
    def default(cls):
        return cls(
            ROOT.joinpath(defaults.SASS_SRC_DIR, 'scss'),
            ROOT.joinpath(defaults.SASS_BUILD_DIR),
            cls.get_default_paths(),
            cls.get_default_functions(),
        )

    def __init__(self, src, dest, include_paths, functions):
        self._src = src
        self._dest = dest
        self._deps = set()
        self._paths = [
            self._src,
        ] + include_paths
        self._functions = functions

    @property
    def paths(self):
        return self._paths

    def __repr__(self):
        return 'Sass({} -> {}, {})'.format(
            self._src,
            self._dest,
            ':'.join(self._paths),
        )

    def get_compile_kwargs(self):
        return {
            'output_style': defaults.SASS_OUTPUT_STYLE,
            'custom_functions': self._functions,
            'include_paths': self._paths,
        }

    def __call__(self, filename=None):
        if filename is not None:
            self._build_file(filename)
        else:
            self._build_all()

    def _build_file(self, filename):
        info('Build %s', filename)
        kwargs = self.get_compile_kwargs()

        infile = self._src.joinpath(filename)
        result = libsass.compile(filename=infile, **kwargs)
        relative_infile = os.path.relpath(infile, self._src)

        outfile = self._dest.joinpath(relative_infile)
        if not outfile.parent.isdir():
            outfile.parent.makedirs_p()

        debug('Writing in %s', outfile)
        with open(outfile, 'wb') as out_stream:
            out_stream.write(result.encode('utf-8'))

    def _build_all(self):
        info('Build all')
        kwargs = self.get_compile_kwargs()
        libsass.compile(dirname=(self._src, self._dest), **kwargs)


class Sass(BaseSass):
    def get_compile_kwargs(self):
        kw = super(Sass, self).get_compile_kwargs()
        kw.setdefault('importers', []).append((1, Sass.css_import))
        return kw

    @staticmethod
    def css_import(path):
        if not path.startswith('CSS:'):
            return None

        s = path[4:] + '.css'
        return [(s, '',)]
