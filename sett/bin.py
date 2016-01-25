#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import functools
from paver.easy import path


class NotInstalled(Exception):
    pass


class DirectorySearcher(object):
    def __init__(self, directory):
        self.directory = path(directory)

    def search(self, program):
        bin_path = self.directory.joinpath(program)
        if bin_path.access(os.X_OK):
            return bin_path
        return None

    def __repr__(self):
        return '<DS {}>'.format(self.directory)


class DirectoriesSearcher(object):
    def __init__(self, directories):
        self.directories = [DirectorySearcher(d) for d in directories]

    def search(self, program):
        for directory in self.directories:
            prog = directory.search(program)
            if prog:
                return prog

    def __repr__(self):
        return '<DS {}>'.format(', '.join(d.directory for d in self.directories))


class Which(object):
    NotInstalled = NotInstalled

    def __init__(self, searchers):
        self.searchers = searchers
        self._cache = {}

    def __repr__(self):
        return '<W {}>'.format(', '.join(repr(s) for s in self.searchers))

    def __getattr__(self, program):
        return self.search(program)

    def search(self, program):
        if '/' in program:
            raise ValueError('Program name must not contain a /')

        if program in self._cache:
            return self._cache[program]

        for searcher in self.searchers:
            bin_path = searcher.search(program)
            if bin_path:
                self._cache[program] = bin_path
                return bin_path

        raise NotInstalled(program)


def default_searchers():
    searchers = []
    from sett.pip import VENV_BIN
    if VENV_BIN.exists():
        searchers.append(DirectorySearcher(VENV_BIN))

    from sett.npm import NODE_MODULES
    if NODE_MODULES.exists():
        searchers.append(DirectorySearcher(NODE_MODULES.joinpath('.bin')))

    from sett.gem import GEM_HOME
    if GEM_HOME.exists():
        searchers.append(DirectorySearcher(GEM_HOME.joinpath('bin')))

    if os.environ.get('PATH'):
        searchers.append(DirectoriesSearcher(os.environ['PATH'].split(':')))

    return searchers


class LazyWhich(object):
    NotInstalled = NotInstalled

    def __init__(self, searchers_provider):
        self.sp = searchers_provider

    def is_evaluated(self):
        return '_which' in self.__dict__

    def __getattr__(self, attr):
        if not self.is_evaluated():
            self._which = Which(self.sp())
        return getattr(self._which, attr)

    def __repr__(self):
        return self.__getattr__('__repr__')()

    def update(self, fn=None):
        if fn:
            @functools.wraps(fn)
            def inner_update(*args, **kw):
                r = fn(*args, **kw)
                self.update()
                return r

            return inner_update
        elif self.is_evaluated():
            del self._which


which = LazyWhich(default_searchers)
