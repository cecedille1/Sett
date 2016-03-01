# -*- coding: utf-8 -*-

import io

import unittest
try:
    import unittest.mock as mock
except ImportError:
    import mock

from paver.easy import call_task, path
from sett.shell import (
    Executor,
    Line,
    Failed,
    Success,
    Evaluation,
)


class TestLine(unittest.TestCase):
    def test_str(self):
        line = Line.build('a = 1')
        self.assertEqual(str(line), '>>> a = 1')

    def test_instruction_dict(self):
        class A(object):
            pass
        a = A()
        a.value = 1
        a._value = 2

        line = Line.build('_ a')
        l = {'a': a}

        r = line({}, l)
        self.assertEqual(r, Evaluation(line, {'value': 1, '_value': 2}))

    def test_instruction_for(self):
        line = Line.build('for x in range(3): a += x')
        l = {'a': 1}
        line({}, l)
        self.assertEqual(l, {'a': 4, 'x': 2})

    def test_instruction(self):
        line = Line.build('a = 1')
        l = {}
        line({}, l)
        self.assertEqual(l, {'a': 1})

    def test_instruction_context(self):
        line = Line.build('a = b + 1')
        l = {'b': 1}
        line({}, l)
        self.assertEqual(l, {'a': 2, 'b': 1})

    def test_success(self):
        line = Line.build('a = 1')
        self.assertEqual(line({}, {}), Success(line, {'a': 1}, {}))

    def test_evaluation(self):
        line = Line.build('a')
        self.assertEqual(line({}, {'a': 1}), Evaluation(line, 1))


class TestExecutor(unittest.TestCase):
    def test_execute(self):
        Line_ = mock.Mock(spec=Line)
        globals = mock.Mock()

        with mock.patch.multiple('sett.shell', Line=Line_, globals=globals):
            x = Executor(['instruction1'])

        list(x())
        Line_.assert_has_calls([
            mock.call.build('instruction1'),
            mock.call.build()(globals(), {}),
        ])

    def test_execute_many(self):
        def l1(glo, loc):
            loc['v'] = 1
            return 'l1'

        def l2(glo, loc):
            assert loc['v'] == 1
            return 'l2'

        L1 = mock.Mock(side_effect=l1)
        L2 = mock.Mock(side_effect=l2)

        with mock.patch('sett.shell.Line', spec=Line) as Line_:
            Line_.build.side_effect = [L1, L2]
            x = Executor(['instruction1', 'instruction2'])

        res = list(x())
        self.assertEqual(res, ['l1', 'l2'])

    def test_exception(self):
        with mock.patch('sett.shell.Line', spec=Line) as Line_:
            Line_.build.return_value.side_effect = ValueError('OH SNAP')
            x = Executor(['instruction1'])

        with mock.patch('sett.shell.traceback') as tb:
            res = list(x())

        self.assertEqual(res, [Failed(Line_.build.return_value, tb.format_exc())])


class TestExecTask(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patch_executor = mock.patch('sett.shell.Executor')

    def setUp(self):
        self.executor = self.patch_executor.start()

    def tearDown(self):
        self.patch_executor.stop()

    def test_input_arg(self):
        call_task('exec', args=['commands here'], options={'stop_at_exception': True})
        self.executor.assert_called_once_with(['commands here'], stop_at_exception=True)

    def test_input_stdin(self):
        with mock.patch('sys.stdin', io.StringIO(u'commands here\n')):
            call_task('exec', args=['-'], options={'stop_at_exception': True})
        self.executor.assert_called_once_with(['commands here'], stop_at_exception=True)

    def test_input_file_abs(self):
        target = path(__file__).dirname().joinpath('test_shell_input').abspath()
        call_task('exec', args=[target], options={'stop_at_exception': True})
        self.executor.assert_called_once_with(['commands here'], stop_at_exception=True)

    def test_input_file_rel(self):
        target = './' + path(__file__).dirname().joinpath('test_shell_input').relpath()
        call_task('exec', args=[target], options={'stop_at_exception': True})
        self.executor.assert_called_once_with(['commands here'], stop_at_exception=True)
