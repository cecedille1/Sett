# -*- coding: utf-8 -*-

import collections
import optparse

from paver.easy import task, needs, debug, info, consume_nargs, cmdopts
from sett import optional_import


@task
@needs('django_settings')
@consume_nargs(1)
@cmdopts([
    optparse.make_option(
        '-f', '--force',
        action='store_true',
        default=False,
    ),
])
def loaddata(args, options):
    filepath, = args

    deserialize = optional_import('django.core.serializers').deserialize
    with open(filepath, 'r') as handle:
        models_by_class = collections.defaultdict(list)
        related_models = list()

        for model in deserialize('json', handle):
            model_class = model.object.__class__
            models_by_class[model_class].append(model.object)

            for field, values in model.m2m_data.items():
                if values:
                    related_models.append((model.object, field, values))

    from django.db import transaction
    waiting_room = WaitingRoom()

    with transaction.atomic():
        for model_class, models_list in models_by_class.items():
            dependencies = Dependencies.from_model(model_class)
            debug('Needs %s for %s', dependencies, model_class.__name__)

            if model_class in dependencies:
                debug('Circual dependencies for %s, proceed with caution', model_class)

            proceed = Proceed(model_class, models_list)
            waiting_room.enter(dependencies, proceed)

        waiting_room.empty()

        if options.force:
            for proceed, deps in list(waiting_room):
                for dep in deps:
                    def noop():
                        debug('== Force resolve for %s ==', proceed)
                        return dep
                    waiting_room.enter(Dependencies.none(), noop)

        if waiting_room:
            raise RuntimeError('Still some people in the waiting room:\n{}'.format(
                waiting_room))

        for model, field, values in related_models:
            debug('Adding %s to %s(%s)', values, model, field)
            getattr(model, field).add(*values)


class WaitingRoom(object):
    def __init__(self):
        self._present = set()
        self._waiting_room = collections.defaultdict(list)
        self._index = collections.defaultdict(set)

    def __bool__(self):
        return bool(self._waiting_room)

    __nonzero__ = __bool__

    def __str__(self):
        return '\n'.join(
            '- {} waiting for {}'.format(
                proceed,
                ', '.join((
                    '[{}{}.{}]' if dep in self._present else '{}{}.{}'
                ).format(
                    '*' if dependencies.is_optional(dep) else '',
                    dep.__module__,
                    dep.__name__
                )
                    for dep in dependencies
                ),
            )
            for dependencies, proceed in self._waiting_room.items()
        )

    def __iter__(self):
        for dependencies, proceeds in self._waiting_room.items():
            unresolved = [d for d in dependencies if d not in self._present]
            for proceed in proceeds:
                yield proceed, Dependencies(unresolved, [d for d in unresolved if dependencies.is_optional(d)])

    def __repr__(self):
        return '<W {}>'.format(self._waiting_room)

    def _is_ready(self, deps):
        return deps.issubset(self._present)

    def _run(self, action):
        if isinstance(action, Proceed) and action.model_class in self._present:
            return

        debug('>Run %r', action)
        self._dep_is_ready(action())

    def _dep_is_ready(self, dep):
        debug('>%s.%s is ready', dep.__module__, dep.__name__)
        self._present.add(dep)
        for dependencies_set in self._index[dep]:
            if self._is_ready(dependencies_set):
                for action in self._waiting_room.pop(dependencies_set, []):
                    self._run(action)

    def enter(self, dependencies, action):
        if not dependencies or self._is_ready(dependencies):
            self._run(action)
        else:
            self._waiting_room[dependencies].append(action)
            for dep in dependencies:
                self._index[dep].add(dependencies)

    def empty(self):
        while self:
            remaining = dict(self)

            for proceed in list(remaining):
                for p, deps in remaining.items():
                    if p is proceed:
                        continue
                    if proceed.model_class in deps:
                        debug('Skip <%s> because <%s> is in <%s>', p, proceed, deps)
                        del remaining[p]
                        break

            promoted_optional = set()
            for deps in set(remaining.values()):
                if deps.all_optional():
                    promoted_optional.update(deps)

            if not promoted_optional:
                break

            for dep in promoted_optional:
                self._dep_is_ready(dep)


class Proceed(object):
    def __init__(self, model_class, models):
        self.model_class = model_class
        self.models = models

    def __repr__(self):
        return '{} models for {Model.__module__}.{Model.__name__}'.format(
            len(self.models),
            Model=self.model_class
        )

    def __call__(self):
        from django.db import utils, transaction

        try:
            with transaction.atomic():
                self.model_class.objects.bulk_create(self.models)
        except utils.IntegrityError as ie:
            info('An error occured: %s , trying one by one', ie)
            info('Already present are %s', self.model_class.objects.all())
            for model in self.models:
                try:
                    with transaction.atomic():
                        model.save(force_insert=True)
                except utils.IntegrityError as ie:
                    info('Error: cannot insert %s(%s), skip', self.model_class.__name__, model.__dict__)

        return self.model_class


class Dependencies(collections.Set):
    @classmethod
    def from_model(cls, model_class):
        from django.db import models
        values = []
        optional = []
        for f in model_class._meta.get_fields():
            if isinstance(f, (models.ForeignKey, models.ManyToManyField)):
                relation = f.rel.to
                while relation._meta.proxy:
                    relation = relation._meta.proxy_for_model
                values.append(relation)
                if f.null or isinstance(f, models.ManyToManyField):
                    optional.append(relation)
        return cls(values, optional)

    @classmethod
    def none(cls):
        return cls([], [])

    def __init__(self, deps, optional):
        self._deps = frozenset(deps)
        self._optional_deps = frozenset(optional)

    def __bool__(self):
        return len(self) != 0

    __nonzero__ = __bool__

    def __hash__(self):
        return self._deps.__hash__()

    def __eq__(self, other):
        if not isinstance(other, Dependencies):
            return NotImplemented
        return self._deps.__eq__(other._deps)

    def __repr__(self):
        if not self:
            return '[--]'
        return '[{}]'.format(', '.join(
            '{opt}{Model.__module__}.{Model.__name__}'.format(
                Model=Model,
                opt='*' if Model in self._optional_deps else '',
            )
            for Model in self._deps))

    def is_optional(self, Model):
        return Model in self._optional_deps

    def all_optional(self):
        return self._optional_deps == self._deps

    def __contains__(self, value):
        if isinstance(value, Proceed):
            value = value.model_class
        return value in self._deps

    def __iter__(self):
        return iter(self._deps)

    def __len__(self):
        return len(self._deps)

    def issubset(self, other):
        return self._deps.issubset(other)
