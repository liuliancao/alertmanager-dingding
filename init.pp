class dingding {
  include systemd::daemon_reload
  file { "/etc/systemd/system/alertmanager-dingding.service":
    source => "puppet:///modules/dingding/alertmanager-dingding.service",
    ensure => file,
    mode => '0644',
    notify => Class['systemd::daemon_reload'],
  }
  file { "/etc/dingding":
    ensure => directory,
    mode => '0755',
    purge => true,
  }

  file { "/etc/dingding/ding.py":
    source => "puppet:///modules/dingding/ding.py",
    ensure => file,
    purge => true,
    mode => '0700',
  }

  file { "/etc/dingding/ding.json":
    source => "puppet:///modules/dingding/ding.json",
    ensure => file,
    purge => true,
    mode => '0600',
  }

  service { 'alertmanager-dingding':
    ensure => running,
    hasrestart => true,
    hasstatus => true,
    subscribe => [Class['systemd::daemon_reload'], File['/etc/dingding/ding.json']],
  }
}
