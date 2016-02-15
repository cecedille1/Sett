# -*- coding: utf-8 -*-


import tempfile
from paver.path import path


class Tempdir(object):
    """Context manager for a temporary directory"""

    def __init__(self):
        self.temp_dir = None

    def open(self):
        assert self.temp_dir is None
        self.temp_dir = path(tempfile.mkdtemp())
        return self.temp_dir

    def close(self):
        if self.temp_dir is not None:
            self.temp_dir.rmtree()
            self.temp_dir = None

    def __enter__(self):
        return self.open()

    def __exit__(self, exc_value, exc_type, tb):
        self.close()


class LineReplacer(object):
    """
    A tool to replace one or more lines in a file.
    It's an iterator on the line no and the content of the line. The line can
    be changed by assigning it.

    If the pattern is fixed, the :meth:`replace` method will replace all lines
    matching.

    >>> with LineReplacer('setup.py') as setup_py:
    ...     for line_no, line in setup_py:
    ...         if line.startswith('__version__'):
    ...             setup_py[line_no] = line.strip() + '-my-version\n'
    ...     setup_py.replace('import this_lib\n', 'import that_lib as this_lib\n')

    .. warning::

        The lines returned by item, iterator, the arguments to :meth:`replace`
        contains trailing newlines.
    """
    def __init__(self, file, encoding='utf-8'):
        self.file = file
        self.fd = None
        self.lines = None
        self.encoding = encoding

    def open(self):
        self.fd = open(self.file, 'r+', encoding=self.encoding)
        self.lines = self.fd.readlines()
        return self

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.file)

    def __iter__(self):
        if self.lines is None:
            raise RuntimeError('{:r} is not opened')

        return enumerate(self.lines)

    def close(self):
        if self.fd is None:
            return

        try:
            self.fd.seek(0)
            self.fd.truncate()
            self.fd.writelines(self.lines)
        finally:
            self.fd.close()
        self.fd = None

    def __enter__(self):
        return self.open()

    def __exit__(self, exc_value, exc_type, tb):
        if exc_value is None:
            self.close()
        else:
            self.fd.close()

    def replace(self, value, by):
        for i, line in self:
            if line == value:
                self[i] = by
                break
        else:
            raise ValueError('pattern not found')

    def insert(self, line_no, value):
        self.lines.insert(line_no, value)

    def append(self, value):
        self.lines.append(value)

    def __getitem(self, item):
        return self.lines[item]

    def __setitem__(self, item, value):
        self.lines[item] = value
