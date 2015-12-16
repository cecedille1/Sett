# -*- coding: utf-8 -*-


import sys
from sett import task_alternative


@task_alternative(1, 't')
def t1():
    sys.stdout.write('t1\n')


@task_alternative(10, 't')
def t():
    sys.stdout.write('t\n')


# Force the task to be found by the alternative task finder
del t
del t1
