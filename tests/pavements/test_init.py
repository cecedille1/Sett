# -*- coding: utf-8 -*-


import sett  # noqa
from paver.tasks import task, environment

initialized = 0


def init(env):
    assert env is environment
    global initialized
    initialized += 1


@task
def t1():
    assert initialized == 1
    print(1)


@task
def t2():
    assert initialized == 1
    print(2)
