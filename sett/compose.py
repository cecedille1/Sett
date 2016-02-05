# -*- coding: utf-8 -*-

import os

from sett import optional_import
from paver.easy import task, consume_nargs, info

docker_compose = optional_import('compose.cli.command', 'docker-compose')


class DockerCompose(object):
    """
    A docker compose context manager.

    It can start a set of containers described by a docker-compose.yml, stop
    and remove them after.

    >>> with DockerCompose() as infra:
    ...     infra.ip('db')
        172.16.0.2
    """
    def __init__(self, basedir='.', name=None, keep=False, filename='docker-compose.yml'):
        self.project = docker_compose.get_project(
            base_dir=basedir,
            config_path=[filename],
            project_name=name,
        )
        self.keep = keep

    def __repr__(self):
        return '<{} {}>'.format(self.__class__.__name__, self.project.name)

    def environment(self, service):
        container = self._container(service)
        environ = {}
        name = service.upper()

        ignore_env = {'PATH'}
        for key, value in container.environment.items():
            if key in ignore_env:
                continue
            environ['{}_ENV_{}'.format(name, key)] = value

        ip = container.get('NetworkSettings.IPAddress')
        for port in container.ports.keys():
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

    def _run(self, *args, **kw):
        volumes_from = kw.pop('volumes_from')
        binds = kw.pop('binds', None) or {}
        container_value = self.project.client.create_container(
            image='busybox',
            command=args,
            host_config=self.project.client.create_host_config(
                binds={
                    external: {'bind': internal, 'mode': 'rw'}
                    for external, internal in binds.items()
                }
            ),
            **kw
        )
        self.project.client.start(
            container=container_value['Id'],
            volumes_from=volumes_from,
        )
        self.project.client.wait(container_value)
        self.project.client.remove_container(container_value)

    def _container(self, service):
        return self.project.get_service(service).get_container()

    def port(self, service, port):
        return self._container(service).get_local_port(port)

    def ip(self, service):
        return self._container(service).inspect()['NetworkSettings']['IPAddress']

    def up(self):
        self.project.up()

    @property
    def containers(self):
        for service in self.project.get_services():
            yield service.get_container()

    def down(self):
        self.stop()
        if not self.keep:
            self.remove()

    def stop(self):
        self.project.stop()

    def remove(self):
        self.project.remove_stopped(v=True)

    def __enter__(self):
        self.up()

        all_env = {}
        for s in self.project.get_services():
            all_env.update(self.environment(s.name))

        self._prev_env = {k: os.environ.get(k) for k in all_env}
        os.environ.update(all_env)
        return self

    def __exit__(self, exc_value, exc_type, tb):
        for k, v in self._prev_env.items():
            if v is None:
                del os.environ[k]
            else:
                os.environ[k] = self.prev_env[k]
        self.down()
        del self._prev_env


@task
@consume_nargs(1)
def compose(args):
    """Control a docker-compose infrastructure"""
    command, = args

    infra = DockerCompose()

    if command == 'start':
        infra.up()
    elif command == 'stop':
        infra.stop()
    elif command == 'rm':
        infra.remove()
    elif command == 'ip':
        for c in infra.containers:
            info('{} => {}\n'.format(c.name, infra.ip(c.service)))
    elif command == 'logs':
        for c in infra.containers:
            info('Logs from {}:\n================\n\n'.format(c.name))
            info(c.logs().decode('utf-8', 'ignore'))
    else:
        raise RuntimeError('usage: compose {start | stop | logs | ip}')
