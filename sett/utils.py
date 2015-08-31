#!/usr/bin/env python
# -*- coding: utf-8 -*-

from paver.easy import debug


def optional_import(module_name):
    try:
        return __import__(module_name)
    except ImportError:
        return FakeModule(module_name)


class FakeModule(object):
    def __init__(self, name):
        self._name = name

    def __getattr__(self, attr):
        raise RuntimeError('Module {} is not installed'.format(self._name))


class BaseInstalledPackages(object):
    def __init__(self):
        self.packages = None

    def __contains__(self, package):
        if self.packages is None:
            self._evaluate()
        debug('package %s is %s', package, 'installed' if package in self.packages else 'uninstalled')
        return package in self.packages

    def _evaluate(self):
        debug('Evaluating packages list')
        self.packages = set(self.evaluate())
        debug('Installed are %s', ', '.join(self.packages))
