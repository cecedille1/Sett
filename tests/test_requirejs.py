# -*- coding: utf-8 -*-

import os
import io
import unittest

try:
    import unittest.mock as mock
except ImportError:
    import mock

from sett.requirejs import RJSBuilder, RJSBuild, FilesListComparator
from paver.path import path


FS = path(__file__).dirname().joinpath('requirejs')


class TestRJSBuilder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.FS = FS.joinpath('1')
        cls.patch_parallel = mock.patch('sett.requirejs.parallel', name='@parallel')

    def setUp(self):
        self.Parallel = self.patch_parallel.start()
        self.parallel = self.Parallel.return_value

    def tearDown(self):
        self.patch_parallel.stop()

    def test_autodiscover(self):
        rjsb = RJSBuilder('app', '/abc/def')
        self.assertEqual(rjsb.autodiscover(self.FS), ['app/app'])

    def test_call_with_args(self):
        BC = mock.Mock(name='RJSBuild')
        rjsb = RJSBuilder('app', '/abc/def', build_class=BC)
        rjsb(self.FS, ['app/app', 'views/view'])
        BC.assert_called_once_with('app/app', self.FS, ('/abc/def/app/app.js'), mock.ANY, mock.ANY)
        self.parallel.assert_called_once_with(BC.return_value)

    def test_call_without_args(self):
        BC = mock.Mock(name='RJSBuild')
        rjsb = RJSBuilder('app', '/abc/def', build_class=BC)
        rjsb(self.FS, [])
        BC.assert_called_once_with('app/app', self.FS, ('/abc/def/app/app.js'), mock.ANY, mock.ANY)
        self.parallel.assert_called_once_with(BC.return_value)


class TestRJSBuild(unittest.TestCase):
    def setUp(self):
        self.cache = mock.Mock(spec=FilesListComparator)
        self.rjsb = RJSBuild('app/app', '/abc/def', '/ghi/out.js',
                             {'abcd': 'efgh'}, self.cache)

    def test_get_command(self):
        with mock.patch('sett.requirejs.which') as which:
            command = self.rjsb.get_command(abc='def', ghi='klm')

        self.assertEqual(command[0:3], [which.node, which.search.return_value, '-o'])
        self.assertEqual(set(command[3:]), {'abc=def', 'ghi=klm'})

    def test_build(self):
        process = mock.Mock(
            name='r.js',
            stdout=iter([
                b'Requirejs header\n',
                b'--------------\n',
                b'/abc/views/view.js\n',
                b'/abc/app/app.js\n',
            ]),
        )
        process.wait.return_value = 0

        with mock.patch('sett.requirejs.subprocess') as subproc:
            subproc.Popen.return_value = process
            with mock.patch.object(self.rjsb, 'get_command') as get_command:
                self.rjsb.build()

        subproc.Popen.assert_called_once_with(
            get_command.return_value,
            stdout=subproc.PIPE,
        )
        get_command.assert_called_once_with(
            baseUrl='/abc/def',
            mainConfigFile='/abc/def/config.js',
            optimize='uglify2',
            out='/ghi/out.js',
            abcd='efgh',
        )
        self.cache.write.assert_called_once_with([
            '/abc/views/view.js',
            '/abc/app/app.js',
            '/abc/def/config.js',
        ])

    def test_error(self):
        process = mock.Mock(
            name='r.js',
            stdout=iter([
                b'Requirejs error\n',
            ]),
        )

        with mock.patch('sett.requirejs.subprocess') as subproc:
            subproc.Popen.return_value = process
            with mock.patch.object(self.rjsb, 'get_command'):
                with self.assertRaises(RuntimeError):
                    self.rjsb.build()

        process.wait.assert_called_once_with()


class TestFilesListComparator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.FS = FS.joinpath('1')
        cls.cache_file = cls.FS.joinpath('.out.js.files')
        cls.out = cls.FS.joinpath('out.js')

        cls.app = cls.FS.joinpath('app/app.js')
        cls.dep = cls.FS.joinpath('views/view.js')

        cls.dep_utime = cls.dep.stat().st_mtime
        cls.app_utime = cls.app.stat().st_mtime

    @classmethod
    def tearDownClass(cls):
        cls.out.remove()
        cls.cache_file.remove()

        os.utime(cls.dep, (-1, cls.dep_utime))
        os.utime(cls.app, (-1, cls.app_utime))

    def setUp(self):
        with open(self.cache_file, 'w') as files:
            files.write('{}\n'.format(self.dep))
        os.utime(self.app, (-1, 30))
        os.utime(self.dep, (-1, 60))
        os.utime(self.cache_file, (-1, 100))
        self.out.touch()
        os.utime(self.out, (-1, 100))
        self.flc = FilesListComparator(self.out)

    def tearDown(self):
        try:
            os.unlink(self.cache_file)
        except:
            pass

    def test_is_up_to_date_false(self):
        assert self.flc.is_up_to_date() is False

    def test_is_up_to_date_dep(self):
        os.utime(self.dep, (-1, 101))
        assert self.flc.is_up_to_date() is True

    def test_is_up_to_date_missing_dep(self):
        with open(self.cache_file, 'w') as files:
            files.write('{}\n'.format('/abc/def'))
        assert self.flc.is_up_to_date() is True

    def test_is_up_to_date_no_out(self):
        self.out.remove()
        assert self.flc.is_up_to_date() is True

    def test_write(self):
        buffer = io.StringIO()
        with mock.patch('sett.requirejs.open') as open:
            open.return_value.__enter__.return_value.write.side_effect = buffer.write
            self.flc.write(['/abc/views/view.js', '/abc/app/app.js'])
        open.assert_called_once_with(self.cache_file, 'w')
        self.assertEqual(buffer.getvalue(), '/abc/views/view.js\n/abc/app/app.js\n')
