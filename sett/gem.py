#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess

from paver.easy import task, consume_args, call_task, debug, sh, might_call

from sett.paths import ROOT
from sett.bin import which
from sett.utils import BaseInstalledPackages


gem_home = os.environ.get('GEM_HOME')
if gem_home is None:
    GEM_HOME = ROOT.joinpath('gem')
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

        gem_list = subprocess.Popen([
            which.gem,
            'list',
            '--no-verbose',
        ],
            env={
                'GEM_HOME': GEM_HOME,
        },
            stdout=subprocess.PIPE,
        )
        return (k.split()[0].decode() for k in gem_list.stdout)

installed_gems = InstalledGems()


@task
@consume_args
def gem_install(args):
    """Install a gem"""
    gem_command = [
        which.gem,
        'install',
        '--no-user-install',
        '--install-dir', GEM_HOME,
        '--no-ri',
        '--no-rdoc',
    ]
    gem_command.extend(args)
    sh(gem_command)


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
