#!/usr/bin/env python
# -*- coding: utf-8 -*-

from paver.easy import task, consume_nargs, debug, info

from sett.utils import optional_import
docker = optional_import('docker', 'docker-py')


class Container(object):
    def __init__(self, name, client=None):
        self.name = name
        self.client = client or docker.Client()

    def __str__(self):
        return self.name

    def exists(self):
        return self.properties is not None

    def is_started(self):
        if self.properties is None:
            return False
        return self.properties['State']['Running']

    def start(self):
        self.client.start(self.name)

    @property
    def properties(self):
        if not hasattr(self, '_properties'):
            self._properties = self._inspect()
        return self._properties

    def _inspect(self):
        debug('Inspecting container %s', self.name)
        try:
            return self.client.inspect_container(self.name)
        except docker.errors.NotFound:
            return None


@task
@consume_nargs(1)
def docker_started(args):
    name, = args
    c = Container(name)
    if not c.exists():
        info('Container %s does not exists', c)
        return

    if c.is_started():
        info('Container %s is already started', c)
    else:
        info('Starting container %s', c)
        c.start()
