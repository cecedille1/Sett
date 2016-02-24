## Unreleased

### Feature

- pip without args defaults to pip freeze
- pip freeze with args will filter output of pip freeze to the row matching one
  the args
- Nicer debug output in rjs task
- Reworked rjs task, with more options and easier customization



## 0.10.4 (2016-02-22)

### Feature
- sett.utils.dispatch.Dispatcher class
- systemd and systemd_conf tasks
- Critical errors for quality

### Refactoring
- Use Dispatcher in sett.daemon and sett.libsass

### Bugfixes
- Remove the pid file after stopping the daemon
