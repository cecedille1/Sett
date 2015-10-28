#!/usr/bin/env python
# -*- coding: utf-8 -*-
# flake8: noqa

__version__ = '0.6.2'

__all__ = [
    'SettTaskFinder',
    'which',
    'optional_import',
    'parallel',
]

import os
import sys
import importlib

from sett.bin import which
from sett.utils import optional_import
from sett.paths import ROOT
from sett.parallel import parallel
from sett.deploy_context import DeployContext

from paver.path import path
from paver.tasks import environment, Task

ALL_LIBS = [p.namebase for p in path(__file__).dirname().files('*.py')]
DISABLED_LIBS = set(os.environ.get('SETT_DISABLED_LIBS', '').split())
ENABLED_LIBS = set(os.environ.get('SETT_ENABLED_LIBS', '').split())


if environment.pavement:
    DISABLED_LIBS.update(getattr(environment.pavement, 'DISABLED_LIBS', []))
    ENABLED_LIBS.update(getattr(environment.pavement, 'ENABLED_LIBS', []))

sys.path.append(ROOT)


class SettTaskFinder(object):
    def _load(self):
        enabled_libs = ENABLED_LIBS or ALL_LIBS
        for enabled_lib in enabled_libs:
            if enabled_lib in DISABLED_LIBS:
                continue
            try:
                module = importlib.import_module('sett.' + enabled_lib)
                for var in vars(module).values():
                    yield var
            except ImportError:
                pass

    def get_tasks(self):
        for item in self._load():
            if isinstance(item, Task):
                yield item

    def get_task(self, task):
        return


environment.task_finders.append(SettTaskFinder())
