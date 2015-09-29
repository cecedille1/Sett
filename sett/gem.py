#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess

from paver.easy import task, consume_args, call_task, debug, sh, might_call

from sett import defaults, which, ROOT
from sett.utils import BaseInstalledPackages


gem_home = os.environ.get('GEM_HOME')
if gem_home is None:
    GEM_HOME = ROOT.joinpath(defaults.GEM_HOME)
else:
    GEM_HOME = ROOT.joinpath(gem_home)


class InstalledGems(BaseInstalledPackages):
    def __contains__(self, gem):
        if ':' in gem:
            gem, version = gem.split(':', 1)
        return super(InstalledGems, self).__contains__(gem)

    def evaluate(self):
        if not GEM_HOME.exists():
            return []

        env = dict(os.environ)
        env['GEM_HOME'] = GEM_HOME
        gem_list = subprocess.Popen([
            which.gem,
            'list',
            '--no-verbose',
        ],
            env=env,
            stdout=subprocess.PIPE,
        )
        return (k.split()[0].decode() for k in gem_list.stdout)

installed_gems = InstalledGems()


@task
@consume_args
def ruby(args):
    env = dict(os.environ)
    env['GEM_HOME'] = GEM_HOME
    sh([which.ruby] + args, env=env)


@task
@consume_args
def gem(args):
    sh([which.gem] + args)


@task
@consume_args
def gem_install(args):
    """Install a gem"""
    call_task('gem', [
        'install',
        '--no-user-install',
        '--install-dir', GEM_HOME,
        '--no-ri',
        '--no-rdoc',
    ] + args)


@task
@consume_args
@might_call('gem_install')
def gem_check(args):
    """Install a gem if it's not installed"""
    to_install = [gem for gem in args if gem not in installed_gems]
    if to_install:
        call_task('gem_install', args=to_install)
    else:
        debug('Gems are synchonized')
