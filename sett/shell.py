# -*- coding: utf-8 -*-

from paver.easy import task


@task
def shell():
    from IPython import embed
    embed()
