## Unreleased

## 0.11.3 (2016-03-15)

### Bugfixes

- rjs will honor build and builder options

## 0.11.2 (2016-03-15)

### Refactoring

- In rjs, defaults is now named params. Defaults are unified in a dict. Some
  extenal defaults are moved inside this dict.
- rjs build class and builder are found in the defaults

### Features

- New decorator @on_init to add initialization function

### Bugfixes

- YML generation for uwsgi
- Workdir is not set when generating systemd.service
- Bug when using GitInstall

## 0.11.1 (2016-03-01)

###Features

- Instructions can be piped to exec
- Instructions starting with '/' or './' will be read from this file in exec
- uwsgi configuration is written in yml if available

### Refactoring

- Test naming strategies

## 0.11.0 (2016-02-24)

### Feature

- pip without args defaults to pip freeze
- pip freeze with args will filter output of pip freeze to the row matching one
  the args
- Nicer debug output in rjs task
- Reworked rjs task, with more options and easier customization
- Nicer failure notifications when exceptions happen in a @parallel function



## 0.10.4 (2016-02-22)

### Feature
- sett.utils.dispatch.Dispatcher class
- systemd and systemd_conf tasks
- Critical errors for quality

### Refactoring
- Use Dispatcher in sett.daemon and sett.libsass

### Bugfixes
- Remove the pid file after stopping the daemon
