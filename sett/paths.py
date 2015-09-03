#!/usr/bin/env python
# -*- coding: utf-8 -*-

from paver.easy import environment, path


if environment.pavement:
    ROOT = path.getcwd().joinpath(environment.pavement.__file__).dirname()
else:
    ROOT = path.getcwd()

LOGS = ROOT.joinpath('var/log')
