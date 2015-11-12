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


Features
--------

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
