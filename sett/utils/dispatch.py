# -*- coding: utf-8 -*-


import sys
import heapq
import types
import itertools
import functools
import collections

from paver.deps.six import with_metaclass

counter = itertools.count()


class MetaDispatcher(type):
    def __new__(self, name, bases, attrs):
        callbacks = self._collect(attrs)
        for command_name, callback_list in callbacks.items():
            callback_list = sorted(callback_list)
            super_fn = attrs.get(command_name)
            assert super_fn is None or callable(super_fn)

            if super_fn:
                heapq.heappush(callback_list, (0, 0, attrs[command_name]))

            fn = self.fn_factory(sorted(callback_list))
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
    def fn_factory(self, args):
        def fn(self):
            for x, y, fn in args:
                fn(self)
        return fn

    def list(self):
        return [fn
                for name, fn in self.__dict__.items()
                if not name.startswith('_') and callable(fn) and name != 'default'
                ]

    def commands(self):
        return {fn.__name__: fn.__doc__ or fn.__name__ for fn in self.list()}


class Dispatcher(with_metaclass(MetaDispatcher)):
    def on(command, priority=1):
        def decorator(fn):
            assert priority != 0
            fn.__dict__.setdefault('callbacks', []).append((command, priority))
            return fn
        return decorator

    auto = staticmethod(on('auto'))
    on = staticmethod(on)

    @classmethod
    def usage(cls):
        commands = cls.commands()
        return '{name} [{command_names}]\n{command_doc}'.format(
            name=cls.__name__,
            command_names=' | '.join(commands.keys()),
            command_doc='\n'.join('\t- {}: {}'.format(k, v)
                                  for k, v in commands.items()),
        )

    def help(self):
        sys.stdout.write(self.usage())
        sys.stdout.write('\n')

    def default(self, name):
        raise NotImplementedError('Command `{}` does not exist\n Usage: {}'.format(
            name, self.usage(),
        ))

    def __call__(self, command='auto'):
        assert not command.startswith('_'), 'Cannot call private methods'
        cmd = getattr(self, command, None) or functools.partial(self.default, command)
        cmd()
