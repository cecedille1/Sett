#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
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


class DirectoriesSearcher(object):
    def __init__(self, directories):
        self.directories = [DirectorySearcher(d) for d in directories]

    def search(self, program):
        for directory in self.directories:
            prog = directory.search(program)
            if prog:
                return prog


class NodeModulesSearcher(object):
    def __init__(self, directory):
        self.directory = directory

    def search(self, program):
        for bin_path in self._candidates(program):
            if bin_path.access(os.X_OK):
                return bin_path

    def _candidates(self, program):
        return (directory.joinpath('bin', program)
                for directory in self.directory.listdir())


class Which(object):
    def __init__(self, searchers):
        self.searchers = searchers
        self._cache = {}

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
        searchers.append(NodeModulesSearcher(NODE_MODULES))

    from sett.gem import GEM_HOME
    if GEM_HOME.exists():
        searchers.append(DirectorySearcher(GEM_HOME))

    if os.environ.get('PATH'):
        searchers.append(DirectoriesSearcher(os.environ['PATH'].split(':')))

    return searchers


class LazyWhich(object):
    def __init__(self, searchers_provider):
        self.sp = searchers_provider

    def __getattr__(self, attr):
        if '_which' not in self.__dict__:
            self._which = Which(self.sp())
        return getattr(self._which, attr)


which = LazyWhich(default_searchers)
