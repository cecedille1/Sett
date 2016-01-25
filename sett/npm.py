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
@which.update
def npm(args):
    sh([which.npm] + args)


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
    packages = [package for package in args if package not in installed_packages]

    if packages:
        call_task('npm_install', args=packages)
    else:
        debug('NPM packages are installed')
