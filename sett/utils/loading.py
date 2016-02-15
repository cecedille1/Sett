# -*- coding: utf-8 -*-

from paver.easy import debug


def optional_import(module_name, package_name=None):
    """
    Tries to import a module and returns either the module or a proxy class
    that raises when accessing an attribute.

    >>> models = optional_import('django.db.models')
    >>> models.Model
        RuntimeError('module django is not installed')
    """
    try:
        module = __import__(module_name)
        if '.' in module_name:
            for segment in module_name.split('.')[1:]:
                module = getattr(module, segment)
        return module
    except ImportError as ie:
        debug('Cannot import %s: %s', module_name, ie)
        return FakeModule(module_name, package_name)


class FakeModule(object):
    def __init__(self, name, module_name):
        self._name = name
        self._module = module_name

    def __call__(self, *args, **kw):
        self._raise()

    def __repr__(self):
        return 'FakeModule({})'.format(self._name)

    def __bool__(self):
        return False

    def __nonzero__(self):
        return False

    def __getattr__(self, attr):
        self._raise()

    def _raise(self):
        if self._module:
            raise RuntimeError('Module {} provided by {} is not installed'.format(
                self._name, self._module))
        raise RuntimeError('Module {} is not installed'.format(self._name))
