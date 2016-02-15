#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from paver.easy import task, consume_nargs, debug, info, environment

from sett.utils import optional_import, task_name as rename_task
docker = optional_import('docker', 'docker-py')


class Container(object):
    def __init__(self, name, client=None):
        self.name = name
        self.client = client or docker.Client()

    def __str__(self):
        return self.name

    @property
    def ip(self):
        return self.properties['NetworkSettings']['IPAddress']

    def exists(self):
        return self.properties is not None

    def is_started(self):
        if self.properties is None:
            return False
        return self.properties['State']['Running']

    def start(self):
        self.client.start(self.name)
        del self._properties

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

    def environ(self, alias=None):
        return docker_environment(self.properties, alias)


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


def docker_started_task(container_name, alias=None, task_name=None):
    @task
    @rename_task(task_name or container_name)
    def start_docker():
        c = Container(container_name)

        if not c.is_started():
            c.start()
        os.environ.update(c.environ(alias))

    return start_docker


def docker_environment(container_inspect, alias=None, ignore_env={'PATH'}):
    name = (alias or container_inspect['Name'].lstrip('/')).upper()
    environ = {}
    for value in container_inspect['Config']['Env']:
        key, value = value.split('=', 1)
        if key in ignore_env:
            continue
        environ['{}_ENV_{}'.format(name, key)] = value

    ip = container_inspect['NetworkSettings']['IPAddress']
    for port in container_inspect['NetworkSettings']['Ports']:
        number, proto = port.split('/')
        context = {
            'name': name,
            'proto': proto,
            'PROTO': proto.upper(),
            'port': number,
            'addr': ip,
        }
        environ.update({
            '{name}_PORT'.format(**context): '{proto}://{addr}:{port}'.format(**context),
            '{name}_PORT_{port}_{PROTO}'.format(**context): '{proto}://{addr}:{port}'.format(**context),
            '{name}_PORT_{port}_{PROTO}_ADDR'.format(**context): ip,
            '{name}_PORT_{port}_{PROTO}_PORT'.format(**context): number,
            '{name}_PORT_{port}_{PROTO}_PROTO'.format(**context): proto,
        })
    return environ


if docker:
    from sett.task_loaders import RegexpTaskLoader
    environment.task_finders.append(
        RegexpTaskLoader(
            r'^docker\('
            '(\w+)'  # Matches the container name
            '(?::(\w+))?'  # Matches the eventual alias
            '\)$',
            docker_started_task,
        )
    )
