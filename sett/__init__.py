#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import importlib

from sett import defaults
from sett.bin import which
from sett.utils import optional_import
from sett.paths import ROOT
from sett.parallel import parallel
from sett.deploy_context import DeployContext
from sett.task_loaders import TaskAlternative, TaskAlternativeTaskFinder

from paver.path import path
from paver.easy import debug
from paver.tasks import environment, Task

__version__ = '0.11.3'

__all__ = [
    'on_init',
    'which',
    'optional_import',
    'parallel',
    'task_alternative',
    'DeployContext',
]


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


class Initializer(object):
    def __init__(self, environment):
        self.environment = environment
        self._on_init_callbacks = []
        self._initialized = False

    def wrap(self, fn):
        def inner_initializer_wrap(*args, **kw):
            self()
            return fn(*args, **kw)
        return inner_initializer_wrap

    def on_init(self, fn):
        self._on_init_callbacks.append(fn)
        return fn

    def __call__(self):
        if self._initialized:
            return
        for fn in self:
            fn(self.environment)

    def __iter__(self):
        return iter(self._on_init_callbacks)


_initializer = Initializer(environment)
on_init = _initializer.on_init


@_initializer.on_init
def init(environment):
    """
    Initialize the paver
    """
    environment.sett = sys.modules['sett']
    environment.ROOT = ROOT
    environment.defaults = defaults
    environment.deployment = DeployContext
    environment.which = which
    environment.on_init = on_init
    environment.task_finders.extend([
        TaskAlternativeTaskFinder(loader, task_alternative),
        SettTaskFinder(loader),
    ])

    init = getattr(environment.pavement, 'init', None)
    debug('Initializing %s', init)
    if init and callable(init):
        init(environment)


def install_init():
    import paver.tasks
    paver.tasks._process_commands = _initializer.wrap(paver.tasks._process_commands)


sys.modules['sett'] = SettModule(sys.modules['sett'])
sys.path.append(ROOT)
task_alternative = TaskAlternative(environment)
loader = SettTaskLoader(*get_libs())


install_init()
