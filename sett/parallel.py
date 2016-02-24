#!/usr/bin/env python
# -*- coding: utf-8 -*-

import threading
import collections
try:
    import Queue as queue
except ImportError:
    import queue

from sett import defaults
from paver.easy import debug


def parallel(fn=None, **kw):
    def inner_parallel(fn):
        debug('Running %s %s ', 'parallel' if defaults.USE_THREADING else 'linear', fn)
        if not defaults.USE_THREADING or kw.get('n') == 1:
            return Linear(fn, **kw)
        return Threaded(fn, **kw)

    if fn is None:
        return inner_parallel
    return inner_parallel(fn)


class Linear(object):
    def __init__(self, fn, n=1):
        self._fn = fn

    def __call__(self, *args, **kw):
        return self._fn(*args, **kw)

    def wait(self):
        return True

    def for_each(self, iterable):
        for i in iterable:
            self(i)


class Threaded(object):
    INITIAL, STARTED, ENDING, ENDED = range(4)

    def __init__(self, fn, n=4):
        self._fn = fn
        self._queue = queue.Queue()
        self._threads = [threading.Thread(target=self._worker(x)) for x in range(n)]
        self.status = Threaded.INITIAL
        self.failed_tasks = []

    def __repr__(self):
        return 'Threaded({}, {})<{!r}>'.format(len(self._threads), self.status, self._fn)

    def for_each(self, iterable):
        try:
            for i in iterable:
                self(i)
        finally:
            self.wait()

    def start(self):
        assert self.status == Threaded.INITIAL
        debug('Starting %s threads', len(self._threads))
        for t in self._threads:
            t.start()
        self.status = Threaded.STARTED

    def _worker(self, n):
        def worker():
            while True:
                try:
                    args, kw = self._queue.get()
                    if args is None:
                        debug('%s: I see the light at the end of the tunnel', n)
                        break
                    debug('%s: Got a task', n)
                    self._fn(*args, **kw)
                except Exception as e:
                    self.failed_tasks.append(Failure(args, kw, e))
                finally:
                    debug('%s: Finishing a task', n)
                    self._queue.task_done()

        worker.__name__ = 'Worker {}'.format(n)
        return worker

    def __call__(self, *args, **kw):
        if self.status == Threaded.INITIAL:
            self.start()

        assert self.status == Threaded.STARTED
        self._queue.put((args, kw))

    def wait(self):
        if self.status == Threaded.INITIAL:
            return

        assert self.status == Threaded.STARTED
        self.status = Threaded.ENDING

        self._queue.join()

        for t in self._threads:
            self._queue.put((None, None))

        debug('Waiting threads')
        for t in self._threads:
            t.join()

        self.status = Threaded.ENDED
        if self.failed_tasks:
            raise RuntimeError('Those tasks failed: {}'.format(
                '\n--\n'.join('{}{!r}'.format(self._fn, ft) for ft in self.failed_tasks)
            ))
        return True


class Failure(collections.namedtuple('_Failure', ['args', 'kw', 'e'])):
    def __repr__(self):
        return '({args}{comma}{kwargs})\n => {e.__class__.__name__}({e})'.format(
            comma=',' if self.args and self.kw else '',
            args=', '.join(repr(a) for a in self.args),
            kwargs=', '.join('{}={!r}'.format(k, v) for k, v in self.kw.items()),
            e=self.e
        )
