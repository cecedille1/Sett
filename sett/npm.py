#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
import json

from paver.easy import debug, task, consume_args, call_task, sh, might_call

from sett import which, ROOT
from sett.utils import BaseInstalledPackages


def get_root():
    root = ROOT
    while True:
        if root == '/':
            break
        node_modules = root.joinpath('node_modules')
        if node_modules.isdir():
            break
        root = root.parent
    else:
        node_modules = ROOT.joinpath('node_modules')

    debug('Node modules is %s', node_modules)
    return node_modules


NODE_MODULES = get_root()


class InstalledPackages(BaseInstalledPackages):
    def __init__(self, glob=False):
        super(InstalledPackages, self).__init__()
        self.glob = glob

    def evaluate(self):
        cmd = [which.npm]
        if self.glob:
            cmd.append('-g')

        cmd.extend([
            'ls',
            '--json',
            '--depth=0'
        ])
        package_list = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            universal_newlines=True,
        )
        packages = json.load(package_list.stdout)
        return set(packages.get('dependencies', []))


installed_packages = InstalledPackages()
global_installed_packages = InstalledPackages(glob=True)


@task
@consume_args
def npm(args):
    sh([which.npm] + args)
    which.update()


@task
@consume_args
def npm_install(args):
    """Install a npm package"""
    call_task('npm', ['install'] + args)


@task
@might_call('npm_install')
@consume_args
def npm_check(args):
    """Install a npm package if it's not installed"""
    packages = [package for package in args
                if package not in installed_packages and
                package not in global_installed_packages]

    if packages:
        call_task('npm_install', args=packages)
    else:
        debug('NPM packages are installed')
