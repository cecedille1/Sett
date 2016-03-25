# -*- coding: utf-8 -*-

import time
import os.path
import collections
import importlib
import traceback
import threading

from sett import optional_import, defaults, ROOT
from sett.utils.dispatch import Dispatcher
from paver.easy import task, info, debug, consume_args, path, error
from paver.deps.six import string_types, moves

observers = optional_import('watchdog.observers')
events = optional_import('watchdog.events')
libsass = optional_import('sass', 'libsass')


# Time to wait for additional events in seconds
DEBOUNCE_WAIT = 0.250


class SassDispatcher(Dispatcher):
    def __init__(self):
        self._sass = Sass.default()

    @Dispatcher.auto
    @Dispatcher.on('watch', -1)
    def compile(self):
        """Launches the compilation of all sass files"""
        debug('Building all files with %s', self._sass)
        self._sass()

    def watch(self):
        """Watches the sass source directories and launches compilation as needed"""
        debug('Building/watching with %s', self._sass)
        try:
            watcher = Watcher(self._sass)
            info('Starting watch %s', self._sass)
            watcher()
        except KeyboardInterrupt:
            pass


@task
@consume_args
def sass(args):
    """
    Usage: sass [compile|watch]

    Shortcut to sassc_watch and sassc_compile.
    """
    sd = SassDispatcher()
    sd(*args)


@task
def sassc_compile():
    """Compile the sass files"""
    sd = SassDispatcher()
    sd.compile()


@task
def sassc_watch():
    """Watch the filesystem for modifications and run sass if needed"""
    sd = SassDispatcher()
    sd.watch()


class EventDispatcher(object):
    """Watchdog compatible event dispatcher. It calls the builder when a file
    is modified and have the right extension"""
    def __init__(self, queue):
        self.extensions = {'.css', '.scss'}
        self.queue = queue

    def dispatch(self, event):
        #  events.FileCreatedEvent triggers FileModifiedEvent
        debug(event)
        if isinstance(event, (events.FileModifiedEvent)) and event.src_path in self:
            self.queue.put(event.src_path)

    def __contains__(self, path):
        stem, ext = os.path.splitext(path)
        if ext not in self.extensions:
            return False
        return True


class Watcher(object):
    """Watchdog compatible event dispatcher. It can be called in the same
    thread or started in another thread.

    >>> with Watcher(Sass.default()):
    ...     call_task('runserver')  # Running an http server and building at the same time

    >>> w = Watcher(Sass.default())
    >>> w()  # Blocks until it's stopped
    """
    def __init__(self, builder):
        self.observer = observers.Observer()
        self.queue = moves.queue.Queue()
        self._thread = None
        self._stop = object()

        self.watches = {}
        for filepath in builder.paths:
            watch = self.observer.schedule(EventDispatcher(self.queue), filepath, recursive=True)
            debug('Watching %s', filepath)
            self.watches[filepath] = watch
        self.builder = builder

    def start(self):
        self.start_observer()
        assert self._thread is None
        self._thread = threading.Thread(target=self.run)
        self._thread.start()

    def stop(self):
        self.stop_observer()
        self.queue.put(self._stop)
        self._thread.join()

    def __call__(self):
        self.start_observer()
        debug('Processing loop')
        try:
            self.run()
        finally:
            self.stop_observer()

    def run(self):
        while True:
            path = self.queue.get()
            if path is self._stop:
                break

            paths = set()
            first_event = time.time()
            try:
                # Debounce: capture all events occuring 250ms after the fist
                delay = DEBOUNCE_WAIT
                while delay > 0:
                    paths.add(self.queue.get(timeout=delay))
                    delay = first_event - time.time() + DEBOUNCE_WAIT

            except moves.queue.Empty:
                pass

            if self._stop in paths:
                break

            for path in paths:
                try:
                    self.builder(path)
                except:
                    traceback.print_exc()

    def start_observer(self):
        debug('Start observer')
        self.observer.start()

    def stop_observer(self):
        debug('Stop observer')
        self.observer.stop()
        self.observer.join()

    def __enter__(self):
        self.start()

    def __exit__(self, exc_value, exc_type, tb):
        self.stop()


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
        if path(filename).basename().startswith('_'):
            return

        kwargs = self.get_compile_kwargs()
        infile = self._src.joinpath(filename)
        try:
            result = libsass.compile(filename=infile, **kwargs)
        except Exception as e:
            error('Cannot build %s: %s', infile, e)
            raise
        relative_infile = os.path.relpath(infile, self._src)

        outfile = self._dest.joinpath(relative_infile).stripext() + '.css'
        if not outfile.parent.isdir():
            outfile.parent.makedirs_p()

        info('Build %s -> %s', filename, outfile)
        with open(outfile, 'wb') as out_stream:
            out_stream.write(result.encode('utf-8'))

    def _build_all(self):
        for filename in path(self._src).walkfiles():

            if filename.ext in {'.scss', '.sass'} and not filename.basename().startswith('_'):
                self._build_file(filename)


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
