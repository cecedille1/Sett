# -*- coding: utf-8 -*-

from __future__ import absolute_import

import ast
import sys
import collections
import traceback
import optparse

from paver.easy import task, environment, consume_nargs, cmdopts

if sys.version_info > (3, ):
    text_type = str

    def text_repr(fn):
        return fn
else:
    text_type = unicode

    def text_repr(fn):
        fn.__name__ = '__unicode__'
        return fn


def shell():
    from IPython import embed
    embed()

if environment.get_task('shell') is None:
    shell = task(shell)


try:
    import builtins
    _exec = getattr(builtins, 'exec')
except (ImportError, AttributeError):
    def _exec(code, globals, locals):
        exec('exec code in globals, locals')


class Line(collections.namedtuple('Line', ['ast', 'original'])):
    @classmethod
    def build(cls, original):
        stripped = original.strip()
        try:
            parsed = ast.parse(stripped, mode='eval')
            return Expression(parsed, original)
        except SyntaxError:
            parsed = ast.parse(stripped)
            return Statement(parsed, original)

    @text_repr
    def __str__(self):
        return u'>>> {}'.format(self.original)


class Statement(Line):
    def __call__(self, globals, locals):
        previous = locals.copy()
        _exec(self.code, globals, locals)
        return self._find_changes(previous, locals)

    def _find_changes(self, previous, current):
        changes, additions = {}, {}
        for k, v in current.items():
            if k not in previous:
                additions[k] = v
            elif previous[k] != v:
                changes[k] = (previous[k], v)
        return Success(self, additions, changes)

    @property
    def code(self):
        return compile(self.ast, self.original.encode('utf-8'), 'exec')


class Expression(Line):
    def __call__(self, globals, locals):
        return Evaluation(self, eval(self.code, globals, locals))

    @property
    def code(self):
        return compile(self.ast, self.original, 'eval')


class Failed(collections.namedtuple('Failed', ['line', 'error'])):
    @text_repr
    def __str__(self):
        return u'{}\n{}'.format(self.line, self.error)


class Success(collections.namedtuple('Success', ['line', 'additions', 'changes'])):
    @text_repr
    def __str__(self):
        buff = [text_type(self.line)]
        for k, v in self.additions.items():
            buff.append(u'    {}: {}'.format(k, v))
        for k, (v1, v2) in self.changes.items():
            buff.append(u'    {}: {} -> {}'.format(k, v1, v2))
        return u'\n'.join(buff)


class Evaluation(collections.namedtuple('Evaluation', ['line', 'evaluation'])):
    @text_repr
    def __str__(self):
        return u'{}\n    {}'.format(self.line, self.evaluation)


class Executor(object):
    """
    A step by step python code executor.

    It executes line by line a line of instructions separated by a ; and yields
    a detailled version of the results of the operation.
    """

    def __init__(self, code, stop_at_exception=True):
        self._locals = {}
        self._globals = globals()

        if not isinstance(code, text_type):
            code = code.decode(sys.getfilesystemencoding())

        self._code = [Line.build(line) for line in code.split(u';')]
        self._continue = not stop_at_exception

    def __call__(self):
        for code in self._code:
            try:
                yield code(self._globals, self._locals)
            except Exception:
                yield Failed(code, traceback.format_exc())
                if not self._continue:
                    break


def _rename(fn):
    fn.__name__ = 'exec'
    return fn


@task
@consume_nargs(1)
@cmdopts([
    optparse.make_option(
        '-c', '--continue',
        action='store_false',
        default=True,
        dest='stop_at_exception',
        help='Keep running when an exception is raised',
    )
])
@_rename
def exec_(args, options):
    """
    Execute a snippet.

    This commands takes a list of python instructions and executes it, one at a
    time showing the results. The valid instructions are single lines or 2
    lines blocks.

    The line can be either an expression or a generic statement. Expressions
    (at the AST meaning) do not intend to modify the locals variables and are
    queries of the local state. They print the evaluation of the expression.
    The rest of the statements are executed and the modifications apported to
    the locals variables are printed (variables added, and variables being changed)

    The lines are all parsed before execution and SyntaxErrors are raised
    before running. When the ``-c|--continue`` flag is enabled, the execution
    continues if an exceptions occurs.

    $ paver exec 'import sys; sys.version; sys, abc = None, sys'
    ---> sett.shell.exec
    >>> import sys
        sys: <module 'sys' (built-in)>
    >>>  sys.version
        2.7.10 (default, Sep  7 2015, 13:51:49)
    [GCC 5.2.0]
    >>>  sys, abc = None, sys
        abc: <module 'sys' (built-in)>
        sys: <module 'sys' (built-in)> -> None

    Exceptions and their tracebacks are printed

    $ paver exec 'open("/tmp/abc", "G")'
    ---> sett.shell.exec
    >>> open("/tmp/abc", G)
    Traceback (most recent call last):
    File "sett/shell.py", line 101, in __call__
        yield code(self._globals, self._locals)
    File "sett/shell.py", line 64, in __call__
        return Evaluation(self, eval(self.code, globals, locals))
    File "open("/tmp/abc", "G")", line 1, in <module>
    ValueError: mode string must begin with one of 'r', 'w', 'a' or 'U', not 'G'

    Exec can handle simple 2 lines if, with, for, ... blocks.
    $ paver exec 'for x in "abc": print(x)'
    ---> sett.shell.exec
    a
    b
    c
    >>> for x in "abc": print(x)
        x: c
    """
    x = Executor(args[0], stop_at_exception=options.stop_at_exception)
    for r in x():
        sys.stdout.write(u'{}\n'.format(r))
