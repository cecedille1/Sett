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

ALL_LIBS = [p.namebase for p in path(__file__).dirname().files('*.py')]
DISABLED_LIBS = set(os.environ.get('SETT_DISABLED_LIBS', '').split())
ENABLED_LIBS = set(os.environ.get('SETT_ENABLED_LIBS', '').split())


if environment.pavement:
    DISABLED_LIBS.update(getattr(environment.pavement, 'DISABLED_LIBS', []))
    ENABLED_LIBS.update(getattr(environment.pavement, 'ENABLED_LIBS', []))

sys.path.append(ROOT)


task_alternative = TaskAlternative(environment)


class SettTaskFinder(object):
    def __init__(self, enabled_libs, disabled_libs):
        self.enabled_libs = enabled_libs
        self.disabled_libs = disabled_libs

    def _load(self):
        for enabled_lib in self.enabled_libs:
            if enabled_lib in self.disabled_libs:
                continue
            try:
                module = importlib.import_module('sett.' + enabled_lib)
                for var in vars(module).values():
                    yield var
            except ImportError as ie:
                debug('Error loading %s: %s', module, ie)
                pass

    def get_tasks(self):
        for item in self._load():
            if isinstance(item, Task):
                yield item

    def get_task(self, task):
        return


environment.task_finders.extend([
    TaskAlternativeTaskFinder(loader, task_alternative),
    SettTaskLoader(environment, ENABLED_LIBS or ALL_LIBS, DISABLED_LIBS),
])
