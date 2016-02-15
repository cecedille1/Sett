# -*- coding: utf-8 -*-

import heapq
import re
import collections
from paver.tasks import Task


class TaskAlternativeTaskFinder(object):
    def __init__(self, loader, ta):
        self.loader = loader
        self.ta = ta

    def __repr__(self):
        return 'TaskFinder<{}>'.format(self.ta)

    def get_tasks(self):
        self.loader.get_tasks()
        return list(self.ta)

    def get_task(self, name):
        self.loader.get_tasks()
        if name not in self.ta:
            return None
        return self.ta[name]


class TaskAlternative(object):
    def __init__(self, env):
        self._env = env
        self._alternatives = collections.defaultdict(list)
        self.poisonned = False

    def __repr__(self):
        return '; '.join(
            '{}: {}'.format(
                name, ', '.join('{}({})'.format(fn.shortname, w) for w, fn in alts)
            )
            for name, alts in self._alternatives.items()
        )

    def __iter__(self):
        for name in self._alternatives:
            yield self[name]

    def __contains__(self, name):
        return name in self._alternatives

    def __getitem__(self, name):
        best = heapq.nsmallest(1, self._alternatives[name])
        if not best:
            raise KeyError(name)
        weight, fn = best[0]
        return fn

    def __call__(self, weight, name=None):
        def decorator(fn):
            if not isinstance(fn, Task):
                fn = Task(fn)
            heapq.heappush(self._alternatives[name or fn.shortname], (weight, fn))
            return fn
        return decorator


class RegexpTaskLoader(object):
    def __init__(self, regexp, task_factory):
        self.task_re = re.compile(regexp)
        self.task_factory = task_factory

    def get_tasks(self):
        return []

    def get_task(self, task_name):
        matching = self.task_re.match(task_name)
        if matching is None:
            return None
        return self.task_factory(*matching.groups(), task_name=task_name)
