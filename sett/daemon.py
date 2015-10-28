# -*- coding: utf-8 -*-

import os
import functools
import signal
import time
import subprocess
import collections

from paver.easy import path, info, consume_nargs, task, debug

from sett import ROOT


RUN_DIR = ROOT.joinpath('var/pid/')


def ctl_task(fn):
    daemons = fn()
    if not daemons:
        return

    @task
    @consume_nargs(2)
    @functools.wraps(fn)
    def ctl(args):

        arg, service = args
        daemons_group = daemons[service]
        if arg in ('start', 'stop', 'restart'):
            daemons_group.call(arg)
        elif arg == 'status':
            for daemon in daemons_group:
                info('* {:40}: {}'.format(str(daemon), daemon.status()))
        else:
            info('Bad task: %s', arg)

    return ctl


def daemon_task(fn):
    daemon = fn()
    if not daemon:
        return

    @task
    @consume_nargs(1)
    @functools.wraps(fn)
    def daemon(args):
        command, = args
        daemon.call(command)

    return daemon


class DaemonGroup(object):
    def __init__(self, daemons):
        self._daemons = daemons

    def __repr__(self):
        return '<Daemons {}>'.format(', '.join(d.name for d in self))

    def __iter__(self):
        return iter(self._daemons)

    def __len__(self):
        return len(self._daemons)

    def run(self, *args):
        assert len(self) == 1
        self._daemons[0].run(args)

    def start(self):
        for d in self:
            d.start()

    def stop(self):
        for d in self:
            d.stop()

    def restart(self):
        self.stop()
        self.start()

    def status(self):
        return [d.status() for d in self]

    def call(self, method):
        assert method in ('start', 'stop', 'restart', 'status')
        method = getattr(self, method)
        return method()


class Daemons(object):
    def __init__(self, *daemons, **groups):
        self._daemons = {}
        self._daemons_groups = collections.defaultdict(list)
        self._names = set([None])

        self.register_all(daemons)
        for group, daemons in groups.items():
            self.register_all(daemons, group=group)

    def __iter__(self):
        return iter(self._daemons_groups[None])

    def __getitem__(self, name):
        if name == 'all':
            name = None
        if name not in self._names:
            raise KeyError(name)
        if name in self._daemons_groups:
            return DaemonGroup(self._daemons_groups[name])
        return DaemonGroup([self._daemons[name]])

    def register_all(self, daemons, group=None):
        for d in daemons:
            self.register(d, group)

    def register(self, daemon, group=None):
        assert group is None or isinstance(group, str) and group != 'all'

        if daemon.name in self._names:
            raise ValueError('Daemon name {} is already registered'.format(daemon.name))
        if group in self._daemons:
            raise ValueError('Group name {} is already registered by a daemon'.format(group))
        self._names.add(daemon.name)

        self._daemons_groups[None].append(daemon)
        self._daemons[daemon.name] = daemon
        if group:
            self._names.add(group)
            self._daemons_groups[group].append(daemon)


class Daemon(object):
    def __init__(self, cmd, daemonize=[], pid_file=None, env=None, name=None):
        self.name = name or str(path(cmd[0]).basename())
        self.cmd = cmd
        self.daemonize = daemonize
        self.env = env
        self._pid_file = pid_file

    @property
    def pid_file(self):
        return self._pid_file or RUN_DIR.joinpath(self.name + '.pid')

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Daemon {}>'.format(self.name)

    def status(self):
        pid = self._get_pid()
        if not pid:
            return 'Not running'
        try:
            os.kill(pid, 0)
        except OSError:
            return 'Not running, stale PID file'
        else:
            return 'Running with pid {}'.format(pid)

    def restart(self):
        self.stop()
        self.start()

    def start(self):
        info('Starting %s', self)

        daemonize = self.daemonize
        if callable(daemonize):
            daemonize = daemonize(self.pid_file)
        elif daemonize is None:
            daemonize = []

        process = self.run(daemonize)
        if self.daemonize:
            debug('Waiting for process')
            process.wait()
        elif self.daemonize is None:
            debug('Writing pid in %s', self.pid_file)
            self._set_pid(process.pid)

    def run(self, args):
        if self.env:
            env = dict(os.environ)
            env.update(self.env)
        else:
            env = os.environ

        command = list(self.cmd)
        command.extend(args)

        info('Running %s', ' '.join(command))
        return subprocess.Popen(command, env=env)

    def stop(self):
        info('Stopping %s', self)
        pid = self._get_pid()
        if pid is None:
            info('%s had no PID file or was not running', self.name)
            return

        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            info('%s was not running', self.name)
            return

        for x in range(5, 11):
            time.sleep(2 ** x / 500)
            try:
                os.kill(pid, 0)
            except OSError:
                break
        else:
            info('Program %s did not respond to SIGKILL, sending SIGTERM', pid)
            os.kill(pid, signal.SIGTERM)

    def _get_pid(self):
        try:
            with open(self.pid_file, 'r') as pid_file:
                return int(pid_file.read().strip())
        except IOError:
            return

    def _set_pid(self, pid):
        with open(self.pid_file, 'w') as pid_file:
            pid_file.write(str(pid))

    def call(self, method):
        assert method in ('start', 'stop', 'restart', 'status', 'run')
        method = getattr(self, method)
        return method()
