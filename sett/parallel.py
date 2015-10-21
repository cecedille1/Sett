#!/usr/bin/env python
# -*- coding: utf-8 -*-

import threading
try:
    import Queue as queue
except ImportError:
    import queue

from sett import defaults
from paver.easy import debug


def parallel(fn):
    if defaults.USE_THREADING:
        return Threaded(fn)
    return Linear(fn)


class Linear(object):
    def __init__(self, fn):
        self._fn = fn

    def __call__(self, *args, **kw):
        return self._fn(*args, **kw)

    def wait(self):
        return True

    def for_each(self, iterable):
        for i in iterable:
            self(i)


class Threaded(object):
    def __init__(self, fn, n=4):
        self._fn = fn
        self._queue = queue.Queue()
        debug('Starting %s threads', n)
        self._threads = [threading.Thread(target=self._worker(x)) for x in range(n)]
        self.started = False

    def for_each(self, iterable):
        for i in iterable:
            self(i)
        self.wait()

    def start(self):
        debug('Starting')
        for t in self._threads:
            t.start()
        self.started = True

    def _worker(self, n):
        def worker():
            while True:
                try:
                    args, kw = self._queue.get()
                    if args is None:
                        break
                    debug('%s: Got a task', n)
                    self._fn(*args, **kw)
                    debug('%s: Finishing a task', n)
                finally:
                    debug('%s: I see the light at the end of the tunnel', n)
                    self._queue.task_done()
        return worker

    def __call__(self, *args, **kw):
        if not self.started:
            self.start()
        self._queue.put((args, kw))

    def wait(self):
        if not self.started:
            return

        self._queue.join()

        for t in self._threads:
            self._queue.put((None, None))

        debug('Waiting threads')
        for t in self._threads:
            t.join()

        return True
