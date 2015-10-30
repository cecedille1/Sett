# -*- coding: utf-8 -*-

from paver.easy import task, environment


def shell():
    from IPython import embed
    embed()

if environment.get_task('shell') is None:
    shell = task(shell)
