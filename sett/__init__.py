#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = '0.9.15'

__all__ = [
    'which',
    'optional_import',
    'parallel',
    'task_alternative',
    'DeployContext',
]

import os
import sys
import importlib

from sett import defaults
from sett.bin import which
from sett.utils import optional_import
from sett.paths import ROOT
from sett.parallel import parallel
from sett.deploy_context import DeployContext
from sett.utils import TaskAlternative, TaskAlternativeTaskFinder

from paver.path import path
from paver.easy import debug
from paver.tasks import environment, Task


def get_libs(environ=os.environ, pavement=environment.pavement):
    all_libs = frozenset(p.namebase
                         for p in path(__file__).dirname().files('*.py')
                         if p.basename() != '__init__.py')
    disabled_libs = set(environ.get('SETT_DISABLED_LIBS', '').split())
    enabled_libs = set(environ.get('SETT_ENABLED_LIBS', '').split())

    if pavement:
        disabled_libs.update(getattr(environment.pavement, 'DISABLED_LIBS', []))
        enabled_libs.update(getattr(environment.pavement, 'ENABLED_LIBS', []))

    return enabled_libs or all_libs, disabled_libs


class SettTaskLoader(object):
    def __init__(self, enabled_libs, disabled_libs):
        self.enabled_libs = enabled_libs
        self.disabled_libs = disabled_libs
        self._tasks = None

    def get_tasks(self):
        if self._tasks is None:
            debug('Loading tasks')
            self._tasks = list(self._load())
        return self._tasks

    def _load(self):
        for enabled_lib in self.enabled_libs:
            if enabled_lib in self.disabled_libs:
                continue
            try:
                module = importlib.import_module('sett.' + enabled_lib)
                for var in vars(module).values():
                    if isinstance(var, Task):
                        yield var
            except ImportError as ie:
                debug('Error loading %s: %s', module, ie)
                pass


class SettTaskFinder(object):
    def __init__(self, loader):
        self.loader = loader

    def get_tasks(self):
        return self.loader.get_tasks()

    def get_task(self, task):
        return


class SettModule(object):
    """Proxy the sett module so that from sett import xyz succeeds, but
    dir(sett) when done by paver in environment.get_tasks fails"""

    def __init__(self, module):
        self.__dict__['_module'] = module

    def __getattr__(self, attr):
        return self.__dict__.get(attr, getattr(self._module, attr))

    def __setattr__(self, attr, value):
        self.__dict__[attr] = value


def init():
    """
    Initialize the paver
    """
    environment.sett = sys.modules['sett']
    environment.ROOT = ROOT
    environment.defaults = defaults
    environment.deployment = DeployContext
    environment.task_finders.extend([
        TaskAlternativeTaskFinder(loader, task_alternative),
        SettTaskFinder(loader),
    ])

    init = getattr(environment.pavement, 'init', None)
    if init and callable(init):
        init(environment)


sys.modules['sett'] = SettModule(sys.modules['sett'])
sys.path.append(ROOT)
task_alternative = TaskAlternative(environment)
loader = SettTaskLoader(*get_libs())


init()
