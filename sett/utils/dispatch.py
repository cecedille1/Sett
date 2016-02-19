# -*- coding: utf-8 -*-

"""
A Dispatcher class
==================

The Dispatcher class defines method and links between them. Method can be
called by calling it directly or by calling the dispatcher with the method
name. Calling the dispatcher with an unknown method name will run
Dispatcher.default which raises NotImplementedError by default.

The Dispatcher metaclass keeps an index of the defined methods and curates a
list of avaible functions in .list() and a dict of commands and their doc in
.commands(). Each Dispatcher sub class a usage classmethod that show the human
readable usage of the dispatcher, and a help method that prints the usage on
the stdout.

Methods can be linked with the Dispatcher.on decorator. Dispatcher.on takes the
name of the method that will invoke the decorated method and a priority to
order it amongs other callbacks. The lower the priority is, the earlier it is
executed The method pointed by the name is not required to exist. If it exists
it will be invoked after the methods linked by a negative priority and before
the one with a positive priority.


```
>>> class ProcessDispatcher(Dispatcher):
...    @Dispatcher.on('restart', 1)
...    def start(self):
...        print('starting')
...    @Dispatcher.on('restart', -1)
...    def stopping(self):
...        print('stopping')
>>> ProcessDispatcher().restart()
stop
start
```

Any method can be used for dispatch provided it is not a classmethod and does
not start with an `_`. Method do not take any argument.

Dispatchers have two special methods: auto and default. Auto is called when the
dispatcher is called without any argument. It can be explicitely defined or
implicitely created by @Dispatcher.on('auto') or @Dispatcher.auto.


```
>>> class ProcessDispatcher(Dispatcher):
...     @Dispatcher.auto
...     def foo(self):
...         print('foo')
...     def auto(self):
...         print('bar')
...     @Dispatcher.on('auto', -1)
...     def baz(self):
...         print('baz')
>>> pd = ProcessDispatcher()
>>> pd()
foo
bar
baz
```

The method *default* is called when a dispatcher is called with an unknown
method name. By default it raises a NotImplementedError. Not this only works
when calling the dispatcher with the name and not by accessing an attribute.


```
>>> class MyDispatcher(Dispatcher):
...     def default(self, name):
...         print('Calling', name)
>>> md = MyDispatcher()
>>> md('foobar')
Calling foobar
```

"""


import sys
import heapq
import types
import itertools
import functools
import collections

from paver.deps.six import with_metaclass

__all__ = [
    'Dispatcher',
]

counter = itertools.count()


class MetaDispatcher(type):
    """
    Metaclass for Dispatcher
    """

    def __new__(self, name, bases, attrs):
        callbacks = self._collect(attrs)
        for command_name, callback_list in callbacks.items():
            callback_list = sorted(callback_list)
            super_fn = attrs.get(command_name)
            assert super_fn is None or callable(super_fn)

            if super_fn:
                heapq.heappush(callback_list, (0, 0, attrs[command_name]))

            fn = self._fn_factory(sorted(callback_list))
            if super_fn:
                fn = functools.wraps(super_fn)(fn)
            else:
                fn.__name__ = command_name
                fn.__doc__ = ', then '.join(f[2].__name__ for f in callback_list)

            attrs[command_name] = fn
        return type.__new__(self, name, bases, attrs)

    @classmethod
    def _collect(cls, attrs):
        callbacks = collections.defaultdict(list)
        for attr in attrs.values():
            if isinstance(attr, types.FunctionType):
                events = attr.__dict__.pop('callbacks', [])
                for command, priority in events:
                    heapq.heappush(callbacks[command], (priority, -next(counter), attr))
        return callbacks

    @classmethod
    def _fn_factory(self, args):
        """
        Creates a function that calls each of the function in args
        """
        fns = [fn for x, y, fn in args]

        def fn(self):
            for fn in fns:
                fn(self)

        return fn

    def _list(self):
        all_methods = {}
        for base in reversed(self.__mro__):
            if issubclass(type(base), type(self)):
                all_methods.update(
                    (name, fn)
                    for name, fn in base.__dict__.items()
                    if not name.startswith('_') and
                    callable(fn) and
                    not isinstance(fn, classmethod)
                )
        return all_methods.items()

    def commands(self):
        """
        Lists all dispatchable methods available in this dispatcher class
        """
        return {name: fn.__doc__ or fn.__name__ for name, fn in self._list()}


class BaseDispatcher(with_metaclass(MetaDispatcher)):
    """
    BaseDispatcher does not implements auto and default
    """

    def on(command, priority=1):
        """
        Decorator that sets the function named *command* to call the decorated
        function when the former is called. The calls occur at priority *priority*,
        where the lower priority is called, first and the function named
        command has priority 0 if it is defined.
        """
        def decorator(fn):
            assert priority != 0
            fn.__dict__.setdefault('callbacks', []).append((command, priority))
            return fn
        return decorator

    auto = staticmethod(on('auto'))
    on = staticmethod(on)

    ignored_methods = {'auto', 'default'}

    @classmethod
    def usage(cls):
        """
        Returns the usage as a string
        """
        commands = cls.commands()
        command_names = [c for c in commands if c not in cls.ignored_methods]
        command_names.sort()

        return '{name} [{command_names}]\n{command_doc}'.format(
            name=cls.__name__,
            command_names=' | '.join(command_names),
            command_doc='\n'.join('\t- {}: {}'.format(k, commands[k]) for k in command_names)
        )

    def __call__(self, command):
        assert command not in self.ignored_methods or not command.startswith('_'), 'Cannot call private methods'
        cmd = getattr(self, command)
        cmd()


class Dispatcher(BaseDispatcher):
    """
    The base Dispatcher class.

    When called, instances of dispatcher dispatch the argument amongst the
    defined methods. If not method exists, it calls ``default`` with the name
    of the asked method.

    When called without any argument, it calls the method(s) decorated by
    Dispatcher.auto or named *auto*.
    """
    def help(self):
        """
        Prints the usage
        """
        sys.stdout.write(self.usage())
        sys.stdout.write('\n')

    def default(self, name):
        raise NotImplementedError('Command `{}` does not exist\n Usage: {}'.format(
            name, self.usage(),
        ))

    def __call__(self, command=None):
        assert command is None or command != 'auto'
        command = command or 'auto'
        if not hasattr(self, command):
            return self.default(command)
        return super(Dispatcher, self).__call__(command)
