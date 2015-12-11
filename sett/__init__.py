#!/usr/bin/env python
# -*- coding: utf-8 -*-
# flake8: noqa

__version__ = '0.9.2'

__all__ = [
    'SettTaskFinder',
    'which',
    'optional_import',
    'parallel',
    'task_alternative',
]

import os
import sys
import importlib

from sett.bin import which
from sett.utils import optional_import
from sett.paths import ROOT
from sett.parallel import parallel
from sett.deploy_context import DeployContext
from sett.utils import TaskAlternative, TaskAlternativeTaskFinder

from paver.path import path
from paver.easy import debug
from paver.tasks import environment, Task

ALL_LIBS = frozenset(p.namebase
                     for p in path(__file__).dirname().files('*.py')
                     if p.basename() != '__init__.py')
DISABLED_LIBS = set(os.environ.get('SETT_DISABLED_LIBS', '').split())
ENABLED_LIBS = set(os.environ.get('SETT_ENABLED_LIBS', '').split())


if environment.pavement:
    DISABLED_LIBS.update(getattr(environment.pavement, 'DISABLED_LIBS', []))
    ENABLED_LIBS.update(getattr(environment.pavement, 'ENABLED_LIBS', []))

sys.path.append(ROOT)


task_alternative = TaskAlternative(environment)


class SettTaskLoader(object):
    def __init__(self, enabled_libs, disabled_libs):
        self.enabled_libs = enabled_libs
        self.disabled_libs = disabled_libs
        self._tasks = None

    def get_tasks(self):
        debug('Loading tasks')
        if self._tasks is None:
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


loader = SettTaskLoader(ENABLED_LIBS or ALL_LIBS, DISABLED_LIBS)
environment.task_finders.extend([
    TaskAlternativeTaskFinder(loader, task_alternative),
    SettTaskFinder(loader),
])


class SettModule(object):
    """Proxy the sett module so that from sett import xyz succeeds, but
    dir(sett) when done by paver in environment.get_tasks fails"""

    def __init__(self, module):
        self.__dict__['_module'] = module

    def __getattr__(self, attr):
        return self.__dict__.get(attr, getattr(self._module, attr))

    def __setattr__(self, attr, value):
        self.__dict__[attr] = value

sys.modules['sett'] = SettModule(sys.modules['sett'])
