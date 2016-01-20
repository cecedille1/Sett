#!/usr/bin/env python
# -*- coding: utf-8 -*-


import getpass
import os
import grp
import collections
import itertools

from sett import ROOT, defaults
from paver.easy import environment


class DeployContextInstance(collections.Mapping):
    def __init__(self, values):
        self.values = values

    def __repr__(self):
        return repr(self.values)

    def __getitem__(self, item):
        try:
            return self._get(item)
        except KeyError:
            raise KeyError('''Missing key ``{name}``: try defining it:
from sett import DeployContext
@DeployContext.register
def set_{name_fn}():
    return {{
        '{name}': None
    }}
'''.format(name=item, name_fn=item.replace('.', '_')))

    def _get(self, item):
        values = self.values
        for key in item.split('.'):
            values = values[key]
        return values

    def __iter__(self):
        return iter(self.values)

    def __len__(self):
        return len(self.values)


class DeployContextFactory(object):
    def __init__(self, **kw):
        self._providers = []
        self._defaults = [kw]

    def __iter__(self):
        return itertools.chain(self._defaults, self._providers)

    def register_default(self, provider_fn=None, **kw):
        provider = self._parse(provider_fn, kw)
        self._defaults.insert(0, provider)
        return provider

    def register(self, provider_fn=None, **kw):
        provider = self._parse(provider_fn, kw)
        self._providers.append(provider)
        return provider

    def _parse(sekf, provider_fn, kwargs):
        if provider_fn is None:
            assert kwargs
            return kwargs

        assert callable(provider_fn)
        assert not kwargs
        return provider_fn

    def __call__(self, values=None):
        context = {}
        if values:
            context.update(values)

        for provider in self:
            if callable(provider):
                provider = provider()

            assert isinstance(provider, collections.Mapping)

            for key, value in provider.items():
                if isinstance(value, dict) and key in context:
                    context[key].update(value)
                elif isinstance(value, list) and key in context:
                    context[key].extend(value)
                else:
                    context[key] = value

        return DeployContextInstance(context)

DeployContext = DeployContextFactory()


@DeployContext.register_default
def default_context():
    setup_options = environment.get_task('setup_options')
    if not setup_options.called:
        setup_options()

    name = environment.options.setup.name.lower()
    return {
        'UID': getpass.getuser(),
        'GID': grp.getgrgid(os.getgid()).gr_name,
        'ROOT': ROOT,
        'NAME': name,
        'domain': defaults.DOMAIN_TEMPLATE.format(name=name, env=environment)
    }
