# -*- coding: utf-8 -*-

import unittest

try:
    import unittest.mock as mock
except ImportError:
    import mock

from paver.tasks import environment
from sett.daemon import (
    Daemons,
    DaemonGroup,
    Daemon,
    ctl_task,
)


class TestCtlTask(unittest.TestCase):
    def setUp(self):
        self.daemons = mock.MagicMock(spec=Daemons)
        self.daemons.__getitem__.return_value = mock.MagicMock(spec=DaemonGroup)

        def ctl():
            return self.daemons
        self.ctl = ctl_task(ctl)

    def _call(self, args):
        environment.args = args
        self.ctl()

    def test_start(self):
        self._call(['start', 'abc'])
        self.daemons.__getitem__.assert_has_calls([
            mock.call('abc'),
            mock.call().call('start'),
        ])

    def test_stop(self):
        self._call(['stop', 'abc'])
        self.daemons.__getitem__.assert_has_calls([
            mock.call('abc'),
            mock.call().call('stop'),
        ])

    def test_statuts(self):
        self.daemons.__getitem__.return_value.__iter__.return_value = [
            mock.Mock(spec=Daemon),
            mock.Mock(spec=Daemon),
        ]

        with mock.patch('sett.daemon.info') as info:
            self._call(['status', 'abc'])

        self.daemons.__getitem__.assert_has_calls([
            mock.call('abc'),
        ])
        self.assertEqual(info.call_count, 2)


class TestDaemons(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.d1 = mock.Mock(name='d1', spec=Daemon)
        self.d1.name = 'd1'
        self.d2 = mock.Mock(name='d2', spec=Daemon)
        self.d2.name = 'd2'
        self.d3 = mock.Mock(name='d3', spec=Daemon)
        self.d3.name = 'd3'

    def setUp(self):
        self.daemons = Daemons(
            self.d1,
            g1=[self.d2, self.d3]
        )

    def test_single_daemon(self):
        assert self.daemons['d1'] == DaemonGroup([self.d1])

    def test_single_daemon_of_group(self):
        assert self.daemons['d2'] == DaemonGroup([self.d2])

    def test_group_daemon(self):
        assert self.daemons['g1'] == DaemonGroup([self.d2, self.d3])

    def test_no_daemon(self):
        with self.assertRaises(KeyError):
            self.daemons['g2']

    def test_list(self):
        assert set(self.daemons) == {self.d1, self.d2, self.d3}

    def test_groups(self):
        assert list(self.daemons.groups()) == [DaemonGroup([self.d2, self.d3])]

    def test_all(self):
        assert self.daemons['all'] == DaemonGroup([self.d1, self.d2, self.d3])

    def test_re_register_daemon(self):
        g1 = mock.Mock(name='g1', spec=Daemon)
        g1.name = 'g1'

        with self.assertRaises(ValueError):
            self.daemons.register(g1)

    def test_re_register_group(self):
        d4 = mock.Mock(name='d4', spec=Daemon)
        d4.name = 'd4'

        with self.assertRaises(ValueError):
            self.daemons.register(d4, group='d1')


class TestDaemon(unittest.TestCase):
    def test_guess_name(self):
        d = Daemon(['/usr/bin/sshd', '-d', '-c', '/etc/sshd/sshd_config'])
        assert d.name == 'sshd'

    def test_command(self):
        d = Daemon(['/usr/bin/sshd', '-d', '-c', '/etc/sshd/sshd config'])
        self.assertEqual(d.command, '/usr/bin/sshd -d -c \'/etc/sshd/sshd config\'')

    def test_daemonize_command_callable(self):
        d = Daemon(['/usr/bin/sshd', '-d', '-c', '/etc/sshd/sshd config'],
                   daemonize=lambda pidfile: ['-D', '--pidfile', pidfile],
                   pid_file='/run/pid')
        self.assertEqual(d.daemon_command, '/usr/bin/sshd -d -c \'/etc/sshd/sshd config\' -D --pidfile /run/pid')

    def test_daemonize_command_list(self):
        d = Daemon(['/usr/bin/sshd', '-d', '-c', '/etc/sshd/sshd config'],
                   daemonize=['-D', '--pidfile', '/run/pid'],
                   )
        self.assertEqual(d.daemon_command, '/usr/bin/sshd -d -c \'/etc/sshd/sshd config\' -D --pidfile /run/pid')

    def test_status_running(self):
        d = Daemon(['ls'], pid_file='/run/pid')

        mocks = mock.MagicMock()
        opened = mocks.open.return_value
        opened.__enter__ = opened.__exit__ = mock.Mock(name='catch', return_value=opened)
        mocks.open.return_value.read.return_value = '1109\n'

        with mock.patch.multiple('sett.daemon', os=mocks.os, open=mocks.open):
            status = d.status()

        mocks.assert_has_calls([
            mock.call.open('/run/pid', 'r'),
            mock.call.open().read(),
            mock.call.os.kill(1109, 0),
        ])
        self.assertEqual(status, 'Running with pid 1109')

    def test_status_stopped(self):
        d = Daemon(['ls'], pid_file='/run/pid')

        mocks = mock.MagicMock()
        mocks.open.side_effect = IOError('No such file or directory')

        with mock.patch.multiple('sett.daemon', os=mocks.os, open=mocks.open):
            status = d.status()

        mocks.assert_has_calls([
            mock.call.open('/run/pid', 'r'),
        ])
        self.assertEqual(status, 'Not running')

    def test_status_stale(self):
        d = Daemon(['ls'], pid_file='/run/pid')

        mocks = mock.MagicMock()
        opened = mocks.open.return_value
        opened.__enter__ = opened.__exit__ = mock.Mock(name='catch', return_value=opened)
        mocks.open.return_value.read.return_value = '1109\n'
        mocks.os.kill.side_effect = OSError('oh snap')

        with mock.patch.multiple('sett.daemon', os=mocks.os, open=mocks.open):
            status = d.status()

        mocks.assert_has_calls([
            mock.call.open('/run/pid', 'r'),
            mock.call.open().read(),
            mock.call.os.kill(1109, 0),
        ])
        self.assertEqual(status, 'Not running, stale PID file')
