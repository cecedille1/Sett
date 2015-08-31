#!/usr/bin/env python
# -*- coding: utf-8 -*-

from paver.easy import environment, path


ROOT = path.getcwd().joinpath(environment.pavement.__file__).dirname()
LOGS = ROOT.joinpath('var/log')
