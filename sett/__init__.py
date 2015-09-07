#!/usr/bin/env python
# -*- coding: utf-8 -*-
# flake8: noqa

__version__ = '0.3.3'
from paver.tasks import environment, Task

from sett.npm import *
from sett.build import *
from sett.jenkins import *
from sett.quality import *
from sett.tests import *
from sett.deploy import *
from sett.source import *
from sett.tar import *
from sett.gem import *
from sett.compass import *
from sett.django import *
from sett.pip import *
from sett.bower import *
from sett.uwsgi import *
from sett.docker import *
from sett.install import *
from sett.remote import *
from sett.requirejs import *


class SettTaskFinder(object):
    def __init__(self):
        pass

    def get_tasks(self):
        for item in globals().values():
            if isinstance(item, Task):
                yield item

    def get_task(self, task):
        return


environment.task_finders.append(SettTaskFinder())
