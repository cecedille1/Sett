SETT
====

Sett is a SET of Tasks for paver. The initial scope of the sett project is
django projects with web resources, but it can work with non django project,
non web projects and even non Python projects.


Usage
-----

The easiest way to use Sett is to ``import  sett`` in your pavement.py. Sett
adds itself to the tasks finders of paver. By default all the components of
sett are loaded.

```
    import sett  # noqa
```

This way sett is required for the setup to be run. Sett provides a way to write
a pavement file that works even if sett is not installed. The import is wrapped
in a try that silences ImportError. Sett will load its tasks if it is present.

```
    try:
        import sett  # noqa
    except ImportError:
        pass
```


### Initialisation

If the pavement file contains a function named init, it will run it with the
paver environment.

```
    def init(env):
        env.deployment.register(wsgi_module='my_app.wsgi.application')
```

### Context injection

In order to pass args, sett takes advantage of the context injection feature of
paver and any tasks that has a `defaults`, `ROOT`, `sett` or `deployment` will
respectively get the sett.defaults module, the path of the root of the project,
the sett module or the current DeployContext. It's also possible to import
values directly.

```
    @task
    def reset_logs(ROOT):
        ROOT.joinpath('var', 'log', 'app.log').truncate()
```


Features
--------

### Deploy context

In order to share context to deploy, pavement and registered tasks can register
callbacks and values to generate a global dict of values. A global instance is
generated and is available by the argument ``deployment`` of a task, or by
importing DeployContext from the sett module. Values can be added by calling
``register`` on it. Two kind of values can be register: either a dict of static
values or a callback providing it at runtime. Those two ways are cannot be used
together in the same invocation.

Callbacks invocations must return a mapping of values. They don't take arguments.
DeployContext.register works nicely as a decorator.

DeployContext.register can be called at any moment, after or before loading, in
a separate tasks, etc.

```
    from sett import DeployContext
    DeployContext.register(name='my_app')

    @DeployContext.register
    def provider():
        from my_app import __version__
        return {
            'version': __version__,
        }

    @task
    def load_prod():
        DeployContext.register(mode='prod')
```

The precendence goes to the last registered provider. ``list``s and ``dict``s
are merged and not replaced. The content of the lower precendence list appears
first and values of lower precendence dict are overwritten. Dicts and lists
must be updated with the same type of values or it will raise a TypeError.

```
    from sett import DeployContext
    DeployContext.register(name='my_app', version='1.23')
    DeployContext.register(name='my_best_app', extra=['best_module'])
    DeployContext.register(extra=['other_module'])
    assert DeployContext() == {'name': 'my_best_app', 'version': '1.23',
                                'extra': ['best_module', 'other_module']})
```

When DeployContext is called a Mapping is returned that has all the key from
the various providers merged. A DeployContext can be called with a mapping of
default values. Thoses keys have the lower precendence, but the can enforce
a type of value, as lists, dicts, and other types of values do not merge.
If a key does not exists, a KeyError is raised with an explication and a code
snippet that describe how to provide the missing value.

```
    from sett import DeployContext
    DeployContext.register(name='my_app', version='1.23', extra=['abc'])

    @task
    def foobarize(deployment):
        context = deployment({'extra': []})
        print('FOO: {name}-{version}\nBAR: {}'.format(
            ', '.join(context['extra']),
            **context,
        )
```

### Disabling and enabling libs

Libs can be enabled or disabled by white and black lists. The lists are set in
the environment variables ``SETT_ENABLED_LIBS`` and ``SETT_DISABLED_LIBS`` and
by the Python variables ``DISABLED_LIBS`` and ``ENABLED_LIBS``. The variables
must be set before importing sett.

For enabled and disabled libs, both sources are merged. Disabling has most
precendence over enabling. If a module is mentionned in disabled and enabled,
it wont be loaded.


```
pavement.py:
    ENABLED_LIBS = ['quality', 'shell', 'uwsgi']
    DISABLED_LIBS = ['django']
    import sett  # noqa
```

```
    $ SETT_DISABLED_LIBS='uwsgi' SETT_ENABLED_LIBS='requirejs compass django' paver
```

In this example, task finder will load only requirejs, compass, quality and
shell but wont load uwsgi, nor django.


### Paths

Sett tries to work exclusively with full paths. This way using ``paver -f
/path/to/pavement.py`` works always and its easier to locate the paths when
working with daemons. It provides two utils achieve this objective: ``ROOT`` and
``which``.

ROOT is a path (paver.easy.path) instance pointing to the root of the project.
The root is the directory containing the pavement.py file.

Which is a tool that locates executable. The error message of subprocess in
python 2 is "No such file or directory" and it is infuriating that the "such
file" is not mentioned (it has been made explicit in latest Python 3). Which
tries to locate an executable file with the right name in the directories of
the PATH environment variable and in some project related directories such as
``node_modules/.bin`` and ``gem/bin`` if respectively nodejs and ruby are used.
It searches when an attribute is accessed or when the search method is called.


```
    >>> from sett import which
    >>> which.ls
    /usr/bin/ls
    >>> which.search('bash')
    /bin/bash
```

When the executable is nowhere to be found, a ``NotInstalled`` exception is raised.

### Imports

Some features (docker, remote requests, templates) requires dependencies in
Sett. Those feature are optional. They import their dependencies by using optional_import.
This function returns a proxy to the module and raises an error when a property
is accessed if the module is no installed. This way the error is explicit and
its not required to check that the import actually succeeded.

```
from sett import optional_import
docker = optional_import('docker')

@task
def docker_task():
    c = docker.Client() # May raise a RuntimeError or instanciate a client.
```

### Parallelization

Sett comes with a thread based parallel execution library library. It works
with a function inside a task and runs multiple instance of the function in
threads. A function is decorated with the @parallel decorator. The decorated
function is called with its arguments and the call is queued until a thread is
ready to work. The decorated function's method wait will block until the queue
is empty.

```
@parallel
def notify_supervisor(supervisor, event):
    send_mail(to=supervisor.email, locate


@task
@consume_args
def notify_supervisors(args):
    event, = args

    for supervisor in get_supervisors():
        notify_supervisor(supervisor, event)
    notify_supervisor.wait()
```

The invocation of parallel functions **cannot be paralled or reentrant**, but
distinct parallel functions can be called simultaneously.


### Installation of patched programs

Sett handles the installation of non packaged python programs. The GitInstall
(sett.git.GitInstall) is a util that can install a git hosted package, while
allowing modifications.

It can be used as a context manager, where the enter will clone the repo and
the exit will install the package, unless an exception was raised. It can be
used with its open, install and close methods, or just called.

```
with GitInstall('gitlab.enix.org:grocher/sett.git') as sett_dir:
    # Manipulate file inside sett_dir
# Installation happens

gi = GitInstall('gitlab.enix.org:grocher/sett.git')
gi() # opens, installs and closes

gi = GitInstall('gitlab.enix.org:grocher/sett.git')
gi.patch('path/to/patch.diff')  # implicitely opens
if is_installable:
    gi.install()
gi.close()
```


### Python and other languages

Sett is build to support other languages and their package manager. It
currently includes nodejs and npm, browsers and bower, ruby and gem, python,
pip and virtualenv. The support strategy is to have the packages in a directory
in the project directory, next to the pavement.py file and to proxy the commands
by setting the right environment variables and command lines switch.

```
├── setup.py
├── pavement.py
├── node_modules
│   ├── almond
│   └── r.js
├── gem
│   ├── bin
│   ├── gems
│   └── specifications
└── venv
    ├── bin
    ├── include
    ├── lib
    └── share
```

Most packages managers handled by sett include a xxx_check command (such as
gem_check, npm_check) that install the programs only if it is not already
installed and do that with checking only the local filesystem. (gem and npm
always check the remote repository for update and it takes a ridiculously long
time).

### Sass

Sett include tasks to build .sass and .scss files with libsass. The commands
sassc_compile to build and sassc_watch to build as soon as a scss file is
written. The command ``sass`` is a shortcut to those command.


Theses two groups of commands have each the same effect.

```
    $ paver sass
    $ paver sass compile
    $ paver sassc_compile

    $ paver sassc_watch
    $ paver sass watch

```

Sass is also embedable in a pavement to run while another task is running. Eg
to run the Sass watcher and the web server simultaneously:

```
    from sett.libsass import Watcher, Sass
    with Watcher(Sass.default()):
        call_task('runserver')
```

Sass use some parameters configurable through the ``defaults``. The first
**SASS_SRC_DIR** and **SASS_BUILD_DIR** are the source and the target of sccs
files and the css output directory. The hierarchy of directories inside the
source dir are copied in the build dir. They defaults respectively to compass/
and static/css.

The **SASS_PATH** is a list of path, either as `:` joined string or as a python
list of strings. It defaults to the environment variable SASS_PATH, or to
``bower_components/`` if it exists. This list of paths with the addition of the
src dir are submitted to the compile function of libsass.

The **SASS_FUNCTIONS** is a python dotted module path or list of thoses or a
list of sass.SassFunction or a combination of modules path and SassFunction.
When it is a python dotted module path, this path is imported, and all
SassFunction defined inside are collected. The whole list of SassFunction are used
by libsass to compile the files.

The **SASS_OUTPUT_STYLE** is the style of build: 'compact', cf sass.OUTPUT_STYLES.

### Docker

Sett provides Docker and docker-compose integration. Docker containers can be
mapped to paver tasks and called with ``needs``. A custom `TaskLoader` converts
docker needed containers to a paver task. The syntax is ``docker(`` *container*
``)``. This way, the task will import even if sett is not installed and
degrades with a Task not found error. The syntax is close to the one used by
``docker run --link``. The task can receive an alias with `:alias`. The
container is started if it is stopped but it is not created. If the container
does not exist, the needs will fail with an unhanlded exception.

The environment of the container is merged with the environment of the hosting
process. The \*_PORT_\* and the \*_ENV_\* environment are copied as if it was
run inside a docker.

```
@task
@needs('docker(redis)')
@needs('docker(postgres:db)')
def runserver():
    assert os.environ.get('REDIS_PORT_6379_TCP_ADDR')
    assert os.environ.get('DB_PORT_5432_TCP_ADDR')
    call_task('sett.django.runserver')
```


### Test naming strategies

Sett uses nosetest to run tests. It propose a way to guess the tests to run
from a module, class, or method full dotted path. The auto filters are used to
select the test to run and to filter the ouput of coverage.

The naming strategy can be guessed or set in
``defaults.TESTS_NAMING_STRATEGY``, either by a dotted python path string or by
setting it to a callable directly.
