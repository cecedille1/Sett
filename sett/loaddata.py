# -*- coding: utf-8 -*-

import collections

from paver.easy import task, needs, debug, info, consume_nargs
from sett import optional_import


@task
@needs('django_settings')
@consume_nargs(1)
def loaddata(args):
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

    from django.db import transaction, models
    waiting_room = WaitingRoom()

    with transaction.atomic():
        for model_class, models_list in models_by_class.items():
            dependencies = frozenset(f.rel.to for f in model_class._meta.get_fields()
                                     if isinstance(f, (models.ForeignKey, models.ManyToManyField)))
            debug('Needs %s for %s', dependencies, model_class.__name__)
            proceed = Proceed(model_class, models_list)
            waiting_room.enter(dependencies, proceed)

        if waiting_room:
            raise RuntimeError(repr(waiting_room))

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

    def __repr__(self):
        return '<W {}>'.format(self._waiting_room)

    def _is_ready(self, deps):
        return deps.issubset(self._present)

    def _run(self, action):
        dep = action()
        debug('Run %r', action)
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


class Proceed(object):
    def __init__(self, model_class, models):
        self.model_class = model_class
        self.models = models

    def __repr__(self):
        return '{} models for {}'.format(len(self.models), self.model_class.__name__)

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
