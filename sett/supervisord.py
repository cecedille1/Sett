# -*- coding: utf-8 -*-

import functools

from sett import ROOT, DeployContext, which, defaults
from paver.easy import task, debug, consume_args, sh, info

from sett.daemon import daemon_task, Daemon
from sett.paths import LOGS


SOCKET = ROOT.joinpath('var/run/supervisor.sock')
PIDFILE = ROOT.joinpath('var/run/supervisor.pid')


@task
@consume_args
def supervisorctl(args):
    """Wrapper to launch supervisorctl"""
    sh([
        which.supervisorctl,
        '-c', ROOT.joinpath('etc/supervisord/supervisorctl.conf'),
    ] + args)


@daemon_task
def supervisord():
    """Wrapper to control supervisord"""
    supervisord_conf = ROOT.joinpath(defaults.SUPERVISORDCONF)
    try:
        return Daemon(
            [which.supervisord, '-c', supervisord_conf],
            daemonize=lambda pidfile: ['--pidfile', pidfile],
            pid_file=PIDFILE,
        )
    except which.NotInstalled:
        return


def write_config(path, sections):
    debug('Writting %s', path)
    with open(path, 'w') as supervisord_conf_file:
        for header, instructions in sections.items():
            supervisord_conf_file.write('[{}]\n'.format(header))
            for instruction, value in instructions.items():
                if isinstance(value, bool):
                    value = str(value).lower()
                elif not value:
                    debug('Skipping empty %s', instruction)
                    continue

                supervisord_conf_file.write('{}={}\n'.format(
                    instruction, value))
            supervisord_conf_file.write('\n')


def supervisord_task(fn):
    """
    The configuration files generator. It generates a list of files under
    etc/supervisord, which are all included in supervisord.conf. A file is
    written for each daemon and for each group. It also writes
    supervisorctl.conf which is used by supervisorctl and is not included in
    supervisord.conf

    etc/supervisord
    ├── daemons
    │   ├── nginx.conf
    │   ├── api.conf
    │   ├── celery-worker.conf
    │   └── web.conf
    ├── groups
    │   ├── backend.conf
    │   └── frontend.conf
    ├── supervisorctl.conf
    └── supervisord.conf
    """
    daemons = fn()
    if not daemons:
        return

    @task
    @functools.wraps(fn)
    def supervisordconf():
        ctx = DeployContext()

        includes = []

        daemons_conf_dir = ROOT.joinpath('etc/supervisord/daemons/')
        daemons_conf_dir.makedirs_p()

        for daemon in daemons:
            daemon_conf = daemons_conf_dir.joinpath(daemon.name + '.conf')
            includes.append(daemon_conf)

            info('Writing daemon %s', daemon)
            write_config(daemon_conf, {
                'program:{}'.format(daemon.name): {
                    'command': daemon.command,
                    'environment': ','.join('{}="{}"'.format(key, val) for key, val in daemon.environ.items())
                },
            })

        groups_conf_dir = ROOT.joinpath('etc/supervisord/groups/')
        groups_conf_dir.makedirs_p()

        for group in daemons.groups():
            group_conf = groups_conf_dir.joinpath(group.name + '.conf')
            includes.append(group_conf)

            info('Writing group %s', group)
            write_config(group_conf, {
                'group:{}'.format(group.name): {
                    'programs': ','.join(d.name for d in group),
                }
            })

        supervisorctl_conf = ROOT.joinpath('etc/supervisord/supervisorctl.conf')
        write_config(supervisorctl_conf, {
            'supervisorctl': {
                'serverurl': 'unix://' + SOCKET,
            },
        })

        supervisord_conf = ROOT.joinpath(defaults.SUPERVISORDCONF)
        write_config(supervisord_conf, {
            'rpcinterface:supervisor': {
                'supervisor.rpcinterface_factory': 'supervisor.rpcinterface:make_main_rpcinterface',
            },
            'unix_http_server': {
                'file': SOCKET,
                'chown': '{UID}:{GID}'.format(**ctx),
            },
            'supervisord': {
                'logfile': LOGS.joinpath('supervisord.log'),
                'pidfile': PIDFILE,
            },
            'include': {
                'files': ' '.join(includes),
            }
        })
    return supervisordconf
