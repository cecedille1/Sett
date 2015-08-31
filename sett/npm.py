#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
import json

from paver.easy import debug, task, consume_args, call_task, sh, might_call


from sett.paths import ROOT
NODE_MODULES = ROOT.joinpath('node_modules')


from sett.bin import which
from sett.utils import BaseInstalledPackages


class InstalledPackages(BaseInstalledPackages):
    def evaluate(self):
        package_list = subprocess.Popen([
            which.npm,
            'ls',
            '--json',
            '--depth=0'
        ],
            stdout=subprocess.PIPE,
            universal_newlines=True,
        )
        packages = json.load(package_list.stdout)
        return set(packages.get('dependencies', []))


installed_packages = InstalledPackages()


@task
@consume_args
def npm_install(args):
    """Install a npm package"""
    npm_command = [
        which.npm,
        'install',
    ]
    npm_command.extend(args)
    sh(npm_command)


@task
@might_call('npm_install')
@consume_args
def npm_check(args):
    """Install a npm package if it's not installed"""
    packages = [package for package in args if package not in installed_packages]

    if packages:
        call_task('npm_install', args=packages)
    else:
        debug('NPM packages are installed')
