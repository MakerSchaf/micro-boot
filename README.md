
## micro-boot

Before you spend too much time here just to discover that micro-boot is
not what you want, here is the summary.

 - micro-boot activates an alternative init-system on your Raspberry.

 - Boot times are reduced but you must create service definitions on
   your own.

 - The usual _systemd_-framework is not available (which is part of the
   reason why it boots faster).

 - The system configuration is not touched; no irreversible or difficult
   to reverse changes.

 - Switching between normal _systemd_ boots and micro-boot are simple.

micro-boot is nothing for beginners but also no rocket science.  I
think it is must suitable for USB gadget or appliances.  If you feel
happy administrating a Linux system on the command and/or you have a
strong use-case for reduced boot time you might want to take a look at
it.


#### Compatibility

micro-boot works

 - with Raspbian 12 (bookworm),
 - on Raspberry Pi Zero, Zero W and Zero 2W hardware.

Raspbian 11 seem to provide a completely different environment to pid1
that 12 and needs more adaption (if Raspbian 11 is still a thing).  For
the Pi 4 some networks issues stop micro-boot from working but this
should be a minor thing.


#### Documentation overview

The introduction gives some background information about micro-boot and
is followed by a step-by-step guide consisting of three different
micro-boot environments:

 - Version 0 is the most minimal.  It doesn't activate network
   interfaces and you need a physical keyboard and monitor to login.  If
   you are looking for the best possible green field then you want this.

 - Version 1 adds network support for wifi, cable and/or USB.  You can
   run it as gadget or some kind of network device.

 - Version 2 adds some example network services (_smbd_, _minidlnad_ and
   _httpd_) to make the gadget a network file and DLNA server.

I created some scripts to support administration of the system: _mb_ and
_edit-inittab_ which are described then.  Finally, some different topics
are covered.


## Introduction


### Background

Raspberry Pis run the operating system Raspbian.  This is a Debian-based
distribution with some adaptions for the Raspberry environment, e.g. the
camera or some software packages that are added by default.  But it's
still Debian flavour.  Debian is a multi-purpose distribution supporting
the whole spectrum from home computing to "big servers" - and
Rapsberrys.

#### The problem

What does that mean for the Raspberry Pi?  All models run a solid
operating system but the Pi Zero gets the worst from both worlds: It's
neither something you would normally use as desktop system and it's also
not a server system running in a data center.  I think most often it
runs with a particular function.  The form factor makes it an excellent
gadget hardware but it needs 80 seconds to boot.  This is annoying,
especially when you connect the gadget to a host and nothing happens for
more that a minute.  I attribute this to booting a very general purpose
OS on a too-small hardware.

#### Possible solutions

What can be done to make it boot faster?

 1. The obvious thing is to buy a faster device, a Raspberry Zero 2W.
    It is about the same price as the Zero W but comes with quicker
    hardware.  This doesn't solve the situation for the Zeros you
    already have and resource usage might still be an issue.

 2. Using a smaller distribution that comes with less services is
    another option.  Possible distributions are

     - DietPi: https://dietpi.com/
     - Buildroot: https://buildroot.org/

    The problem here is that you have to replace your working system.
    Depending on what you choose you may have to consider how to install
    software updates.  Such distributions may not be what you want (but
    they are really impressive).

 3. Change the boot process.  When Raspbian boots, it loads _systemd_
    which is preconfigured to load all kind of stuff that's not always
    needed.  Changing to a different init-system - and this is what
    micro-boot does - allows (and requires) to boot the services that
    are really needed.  The main advantages over changing the
    distribution are

     - You keep your distribution and the normal Linux userland is
       available.
     - Changing the system startup does not impact your normal system.
     - Switching to micro-boot and back is simple.

#### Timing

What is the difference?  The following table shows the time from power-on
to MTP device detection by the host.

  | Boot mode    |  Zero   | Zero 2 |
  | ------------ | ------- | ------ |
  | micro-boot   |   20s   |   12s  |
  | systemd      |   36s   |   16s  |

The difference between micro-boot and _systemd_ doesn't look great
mostly because the _systemd_ MTP setup was optimized for speed here
(`After=local-fs.target; DefaultDependencies=no`).

Furthermore, for micro-boot, timing remains the same for other
services:

 - 18 seconds from power-on to the login prompt on the serial interface
   (which does not have a difficult to measure handshake),
 - while the standard _systemd_ serial _agetty_ takes 66 seconds (25
   seconds on Zero 2 hardware).

I guess _systemd_ optimisation could bring similar results than
micro-boot but I consider the deep dive into its documentation to be a
waste of time.  Other differences to a normal Raspbian are used RAM and
number of processes hanging around.


### Approach

Choosing a different init-system is simple on a Raspberry Pi.  All it
takes is that `init=/etc/micro-boot/init` is appended to the kernel
command line in _cmdline.txt_.  This parameter diverts the boot process
from _systemd_ to busybox init where services configurations are read
from _/etc/inittab_ (one line per service, which is the original style
how UNIX services were configured).

busybox init is not the best choice.  There are other init-systems
around and micro-boot could use one of them.  And even in comparison to
the original _init_, busybox init does not look very good because it
implements only a subset of the original.  (Most importantly, busybox
init does not monitor and disable services if the terminate or loop to
fast.  Keep that in mind when you add your own services to the system.)

However, I chose busybox init because

 - its functionality is sufficient, and
 - it is available in the standard Raspbian (and it is the only available
   alternative init-system).

If you like the idea of changing the init-system but not (busybox) init
I think it's not too difficult to adapt micro-boot to another.


### Wireless network

A fresh Raspbian installation uses _NetworkManager_ to connect to the
wireless network but micro-boot is going direct to *wpa_supplicant*.
Its configuration file *wpa_supplicant.conf* does not have any
configuration data and wifi will not work.  The solution is to add
a minimum network configuration to it:

    $ sudo cat /etc/wpa_supplicant/wpa_supplicant.conf
    ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
    update_config=1

    # Country is Germany
    country=DE

    # Only ssid and psk is required.  All strings in double quotes.
    network={
       ssid="Your SSID here"
       psk="The network password"
    }

If you prefer to not modify your system configuration create the file in
_/etc/micro-boot_ and the command line in _inittab_ from

    :w:respawn:wpa_supplicant -c /etc/wpa_supplicant/wpa_supplicant.conf -i wlan0

to

    :w:respawn:wpa_supplicant -c /etc/micro-boot/wpa_supplicant.conf -i wlan0

If micro-boot is already active run `sudo mb reload` or `sudo kill -HUP 1`
to restart *wpa_supplicant* manually.


### Assumptions and prerequisites

 - Your Raspberry should be completely configured.

 - Verify you have configured you wifi network.

 - micro-boot can start a network or MTP gadget but this requires that
   `dtoverlay=dwc2` is added to the Raspberry's _config.txt_.

 - Some of micro-boot configuration files assume in several locations,
   i.e. that

   1. your username is `pi` with _/home/pi_ as home directory: `grep -E
      '\Wpi\W' *`,
   2. your user id is `1000`: `grep 1000 *`, and
   3. files live in _/etc/micro-boot_: `grep micro-boot *`.

   Adjust the files as required.


### Emergency instructions

micro-boot is going to change you system configuration and things might
go wrong.  How can you restore your system?

 1. Take the SD-card and put it into another computer.  Even a Windows
    system will work.

 2. There are two partitions: _boot_ and _root_.  You want the _boot_
    partition which contains the file _cmdline.txt_.

 3. Open _cmdline.txt_ (optional: turn off automatic line wrapping).
    The file contains only one single line (and visible line breaks are
    due to automatic wrapping or a mistake if they are real).

 4. At the end of the line you will find `init=...`.  Delete the text
    starting with `init=` until the end of the line (or the next blank).

 5. Save the file, unmount / eject it properly and use it to boot your
    Raspberry as normal.


## Version 0 - Hello World!


### micro-boot Installation

Installing micro-boot requires two things:

 1. The micro-boot directory must live below _/etc_.

 2. The system's _cmdline.txt_ must be edited to run the _init_ program,
    and _inittab_ must be located in _/etc_.

You have to do the first thing on your own but the _mb_ script helps you
with the second.  You can copy the micro-boot directory to _/etc_.  I
prefer to have the directory somewhere in my home and create a symbolic
link to _/etc_ e.g.

    $ sudo ln -s /home/pi/boot/micro-boot /etc/micro-boot

I think that makes it somewhat easier to change environments.  Once you
have done this you can run _mb_ to modify _cmdline.txt_.  The script
expects the micro-boot directory which you want to use as command line
parameter.

    $ cd /etc/micro-boot
    $ sudo ./mb install /etc/micro-boot

_mb_ expects that _cmdline.txt_ is in _/boot/firmware_ and that this
partition is already mounted.  This might be not the case (and is not in
the micro-boot environment) and you might have to run

    $ sudo mount /boot/firmware

first.

_mb_ will show the old and new versions of _cmdline.txt_ and asks you to
confirm.  Only `y` will do.  All other input will cancel the change.
The directory's _inittab_ is then linked to _/etc_ and _cmdline.txt_ is
updated.  The script will also try to install itself (more precise: _mb_
from the install parameter directory) under _/usr/bin_ by creating a
symbolic link.  An existing link will be removed but a file named _mb_
will not be replaced.


### Verify your setup

Here are some things you should check before booting into micro-boot.
All commands should be executed in _/etc/micro-boot_.

 1. Running `/etc/micro-boot/init` returns `init: must be run as PID 1`.
    If not do `rm init; ln -s /usr/bin/busybox init`.

 2. `/etc/micro-boot/awk -h` shows

        ./awk: invalid option -- 'h'
        BusyBox v1.35.0 (Raspbian 1:1.35.0-4) multi-call binary.
        ...

    plus some more text.  If not do If not do `rm awk; ln -s
    /usr/bin/busybox awk`.

 3. You have set `HAVE_MAKER_PHAT` in _environ_ to `n` unless you have a
    maker-phat connected.  Otherwise the Raspberry will very likely boot
    to serial gadget.

 4. Choose an _inittab_.  micro-boot comes with three different variant:
    0, 1 and 2 (which correspond to the documentation).

    - 0 is for local logins by keyboard and monitor only.

    - 1 is local login plus network configruation and login by ssh.
      This version can run as USB network gadget.

    - 2 is the same as 1 but includes configuration for sample services.

    Do `cp inittab.N inittab` where `N` is your chosen variant.

 5. Check _gadget-mode_.  For USB network it should contain the value
    `rndis`.

 6. Do you plan to login via _ssh_?  Is _sshd_ installed?  If not, run
    `sudo apt-get install openssh-server`.


### Uninstalling

If you want to go back (temporarily or permanently) you can run

    $ sudo mb uninstall

This will

 1. edit _cmdline.txt_, show the different versions and ask for
    confirmation,

 2. remove _/etc/inittab_ if that's a symbolic link, and

 3. remove _/usr/bin/mb_ if that's a symbolic link.

undoing the changes from `install`.  Changing from one micro-boot
directory to another (i.e. installing the other) does not require
uninstallation.


### Changing the directory name

micro-boot comes with various scripts and they reference to the
directory where they are installed.  Usually the shell scripts do this
by

    DIR=${0%/*}

At least that's the way how it should be.  micro-boot's central
configuration file _/etc/inittab_ can't do that and uses the directory
name.  To change the directory you should run

    $ cd /etc/micro-boot
    $ sed -i~ 's|/etc/micro-boot|/etc/my-boot|g' inittab

when _/etc/my-boot_ is the directory you want.  The command changes all
occurrences of the directory overwrites the original file saving this as
*inittab~*.  You might want to omit the `-i~` to see the changes first.

Notice that you do not need root permissions and you are not running the
command on _/etc/inittab_ but on the file in the micro-boot directory.

!! Do not run the above _sed_ command on _/etc/inittab_.  This will
break _mb_'s install / uninstall operations. !!

Since all micro-boot file live in the same directory you can check for
the hard-coded pathname with

    $ grep /etc/micro-boot *

Expect to see the file _environment_ here and change the directory name
appropriately.


### busybox init

_init_ is the original runlevel controller of UNIX and _busybox_ comes
with an applet for it.  The original _init_ (also called SysV init) was
already simple and the _busybox_ reduced even this a little bit.  But
busybox init is good enough to run small installations (embedded
devices, gadgets) and more important: it is the only alternative to
_systemd_ that comes with Raspbian's default distribution.  (E.g.
_runit_ is not compiled into _busybox_.)

When busybox init starts it reads the file _/etc/inittab_ to see, which
services it should start.  busybox init does not know about different
runlevels or targets like SysV init or _systemd_.  But, depending on the
device's function it might be sufficient and there is a word-around.

#### Format of /etc/inittab

Each line of _inittab_ defines one process (or service).  `#`-comments
and empty lines are allowed.  Lines describing a process have exactly
four colon-separated fields, which are

 1. This field holds the device which _init_ should connect to the
    process if one is required.  This function is usually used for
    _getty_ processes..  In SysV init this is the process' id.

 2. This is the SysV init field for runlevel information and is not used
    by busybox init.

 3. The third is the _action_ field. It defines when the process should
    be started, see below.

 4. The final field is the process' command line.  Notice that this is
    not executed by calling a shell interpreter, that is characters like
    `'`, `$` or `*` do not have a special function.

Possible values for the action field are:

 - **sysinit** labels processes that are started after boot.  busybox
   init waits for the process to end before starting another.

 - **wait**: when all sysinit processes are done (from top to bottom),
   these processes are run next.  Again, busybox waits for the processes
   to finish.

 - The **once**-processes are started after the wait processes are
   finished but all once-processes are run in parallel and busybox init
   doesn't wait for them.

 - The **respawn**-processes are the services which should run normally
   on the system.  They are started in parallel and are restarted when
   they exit.  The processes are launched after the once-processes.

A variation of respawn is **askfirst**.  This keyword is used for
_getty_ processes which are only run after a user hit return on a
connected keyboard.  This action is useful for systems with very low
resources where even an idle _getty_ or _sh_ is not wanted.

There are more keywords to handle special situations:

 - **shutdown**: These process entries are run when busybox init are
   executed to shutdown or reboot the system.

 - **restart** defines a single process (only one entry is used) that
   replaces busybox init after it has stopped all running processes.
   (No, it's not possible to start _systemd_ from here, at least it is
   not easy.)

 - **ctrlaltdel** is executed when busybox init gets a SIGINT signal
   which is usually the case when ctrl+alt+del is pressed on the
   keyboard.

#### Interacting with busybox

_systemd_ uses a socket for communication and SysV init has a named pipe
for that.  busybox init has neither.  The only way to communicate with
it is sending signals.

  | Signal    | Function                        |
  | --------- | ------------------------------- |
  | SIGINT    | execute ctrlaltdel actions      |
  | SIGHUP    | reloads /etc/inittab            |
  | SIGQUIT   | execute restart actions         |
  | SIGTERM   | reboot the system               |
  | SIGUSR2   | power off                       |

Notice that the SIGHUP action is optional and must be compiled in.  This
is the case for Raspbian but you need to take care of that when
compiling busybox on your own.

Instead of remembering which signal reboots and which halts you can use
`busybox reboot` and `busybox halt` (always as root) for it.  The normal
`shutdown` will not work since it is bound to _systemd_.

_mb_ (the script that was used to install micro-boot) implements these
actions too with the "added value" of expanding abbreviated action
names.  That is the `p` in `sudo mb p` is understood as `poweroff`.

#### micro-boot inittab

micro-boot's _inittab_ is very basic in this version.  It starts with

    ::sysinit:/etc/micro-boot-2/sysinit

The _sysinit_ script makes all the basic preparations, e.g.

 - setting the fake hardware clock,
 - remounting `/` read-write,
 - setting the hostname,
 - configuring the USB gadget

Lines like

    tty3::askfirst:/bin/bash --login

start a login shell on the physical console (i.e., keyboard and
monitor).  No password is required but the shell must be activated by
pressing return.  The _user-login_ script simplifies logging in a little
bit and is used too:

     tty1::askfirst:/etc/micro-boot/user-login pi

The following line

    ::respawn:/sbin/agetty -l /usr/bin/login 115200 serial0

starts a login process on the Raspberry's serial interface, that is,
username and password is required to access it.  Notice that you have to
enable the interface either by adding `enable_uart=1` in _config.txt_ or
by running `sudo raspi-config`.  Deactivate (or delete) this line if you
do not use the serial interface.


### The running system

These files are used here:

 - inittab: Central configuration file for all services.  The version
   used is _inittab.0_.

 - shutdown: Script to properly shutdown the system.

 - sysinit: This script initialises the system basics, e.g. make `/`
   writeable.

 - user-login: Shell script to setup the console and start a login shell
   for the user.

The process list is very clean:

    $ mb ps
    1 init
    177 login -f
    178 init
    179 init
    180 init
    181 /sbin/agetty -l /usr/bin/login 115200 serial0
    182 busybox syslogd -n
    183 /usr/bin/dbus-daemon --config-file=/usr/share/dbus-1/...
    221 /usr/sbin/gpm -m /dev/input/mice -t exps2
    230 -bash


## Version 1 - Now with network


### Description

The next version uses _inittab.1_ and adds network configuration to the
setup.  The script _configure_ (which is the key element for this
version) is executed and detects which network interfaces are available:

 | Interface                | Configuration  |
 | ------------------------ | ---------------|
 | wired ethernet    eth0   | dhclient       |
 | wireless network  wlan0  | dhclient       |
 | USB network       usb0   | udhcpd         |

_inittab_ is dynamically adjusted to start the services to configure the
interfaces.  Notice that for `usb0` the network configuration itself is
static (169.254.233.90/16) and set in _activate-gadget_.  The DHCP
server is started to configure the gadget's host interface.

_configure_ detects also a serial interface over USB and starts a
_getty_ process if required.

Finally, _configure_ executes `/etc/micro-boot/start rdate`.  The
command waits 20 seconds for the network to come up and connect to
time.nist.gov to set the local time.  This is a work-around and could be
done better - if necessary.

An _sshd_ is started and gives access by network.


### USB Gadget

The USB gadget is activated by _sysinit_ (the script that runs first;
_configure_ comes second) if no device is found on the USB bus.  The
gadget mode is selected by the value of the file _gadget-mode_.  It
must contain one of the following keywords:

  | Keyword     | Gadget mode                     |
  | ----------- | ------------------------------- |
  | eth         | USB ethernet and serial         |
  | mtp         | MTP storage device              |
  | rndis       | USB RNDIS ethernet and serial   |
  | serial      | only serial interface oder USB  |

`mtp` and `rndis` make most sense for a storage device or network
connection.  The serial interface is included in the network modes and
seems to be not compatible with `mtp`.  `eth` works well with Linux
computers but `rndis` works with Windows systems too.

If network is chosen _activate-gadget_ sets the gadget's IP
configuration to 169.254.233.90/16.  This avoids adding up entries to
_known-hosts_.  A DHCP server is started by _init_ but if the host does
not accept or process DHCP and IP from the network can be configured
manually.

When MTP is selected _umtprd_ is started, which uses the configuration
from _umtprd.conf_.  _umtprd_ itself is not part of Raspbian's default
installation and must be added manually.  But the version is also
somewhat older and missing some features so that you might want to
consider to compile a newer version (from Github) on your own.


### Debugging USB network issues

A problem that might occur is that the gadget brings up the network but
your host does not connect.  To check the USB connectivity:

 - Run `ifconfig -a`.  If an interface like `enx222233445566` appears
   then the gadget is properly connected and the host is not bringing it
   up.  `sudo ifconfig enx222233445566 192.168.1.2 netmask 255.255.0.0
   up` might help but still the host's _NetworkManager_ might come into
   your way by setting the interface down again.

 - Run `ls -l /dev/ttyA*`.  If you get _/dev/ttyACM0_ then the USB
   connection works and you can use `cu -l ttyACM0 -s 115200` to connect
   via the serial interface to check things on the gadget.  You might
   need to install _cu_: `apt-get install opencu` and set `TERM=linux`
   on the gadget after logging in.  What you should expect to find is a
   configured `usb0` and a running dhcpd:

       $ ifconfig -a
       ...
       usb0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 169.254.233.90  netmask 255.255.0.0  broadcast 169.254.255.255
       ...
       $ mb ps usb
       254 busybox udhcpd -f -S /etc/micro-boot/usb-dhcpd.conf

 - If USB is completely not working your gadget might have wifi
   activated to login.

If nothing else works, connect keyboard and monitor.


### Files and services

This micro-boot version add some files.

 - activate-gadget: Configure the Raspberry's gadget according to
   _gadget-mode_.  `rndis` is the safe value.

 - configure: The script is run from _init_ to detect the current
   hardware setup and to configure the services, which _init_ should
   start.

 - gadget-mode: Contains a single word setting the Raspberry's gadget
   mode.

 - start: This is a multi-call wrapper script and the first parameter
   set the command to execute.  It is usually called from _init_ and
   applies e.g. shell I/O redirection or variable substitution, which
   cannot be done inside _inittab_.

 - usb-dhcpd: Start the _busybox_ DHCP server on usb0 to configure the
   host's network interface.

 - usb-dhcpd.conf: The configuration file for the USB DHCP server. It is
   automatically created by _usb-dhcpd_.  (This file may be removed in a
   later version.)

Depending on the configuration _init_ starts the following services:

 - Wired network: _dhclient_ on eth0.

 - Wireless network: _wpa_supplicant_ and _dhclient_ on wlan0.

 - USB network: _usb-dhcpd_ on usb0.

 - USB serial interface: _getty_ on _/dev/ttyGS0_.  The host's device
   is _/dev/ttyACM0_.

 - For any kind of network: _avahi-daemon_.  (This requires a running
   _dbus-daemon_ which was already part of version 0.)

Additionally, _init_ start an _sshd_ regardless if network is there or
not.


## Version 2 - Network services


### Description

This micro-boot version is implemented by _inittab.2_ and adds
configuration for some example services.

 - _smbd_ and _nmbd_,
 - busybox httpd

Here you might be going to modify your running system outside of the
micro-boot directory.

  1. You might have to install the services first because they are not
     included in the standard Raspbian distribution.  But you can also
     just read through the documentation and go for the services you
     want.

  2. The services might need to store file somewhere.  I.e., _smbd_
     creates a password file.

  3. The services provide read/write access to your disk and directories
     have to be configured.

Since the services are only suggestions they are disabled by default.


### Installing services

The following instructions explain how to install and setup _smbd_ but
they are also a template if you want to add services on your own.

#### File server

Installing software works in micro-boot as usual because it uses the
same userland as the normal Raspbian.

    $ sudo apt-get update  &&  sudo apt-get install smbd

Notice that when you install a server (whether in the normal Raspbian or
the micro-boot environment) the service is (usually) automatically
activated in the _systemd_ environment.  You have to execute

    $ systemctl disable smbd

to disable the services.  This is also true if you install it from
within micro-boot but _systemctl_ is not working here.

As mentioned above some directories are configured in _smb.conf_ and
have to be created.  Feel free to change them according to what you need
or find best.

 - _/home/pi/tmp/smbd/private_ holds _smbd_'s password database.

 - _/home/pi/tmp/smbd/public-disk_ is a directory for public read-write
   access.  The share name is _disk_.

 - _/home/pi/public_ is the directory behind the share _public_, also
   publicly available but read-only.

 - Finally _/home/pi_ is exported as _private_ share.

Create the directories with the following commands:

    $ mkdir -p /home/pi/tmp/smbd/private /home/pi/tmp/smbd/public-disk
    $ mkdir -p /home/pi/public
    $ chmod 775 /home/pi/tmp/smbd/public-disk

To test your setup run

    $ sudo ./start smbd

(_start_ is used as wrapper around _smbd_.  Do `grep smbd start` to see
what's going on there.)  Give _smbd_ so time to start and try to connect
to the server from your gadget host or from any other computer.  You
should see the three shares:

 - _disk_ allows you to login anonymously, and to read and create files
   and directories as you like,

 - _public_ also does not require a password but gives read-access only.

 - Finally, _private_ requires a password and you have that to set with
   `sudo smbpasswd -c smb.conf -a pi` first.

When you have verified that _smbd_ is working as expected, enable
and start it as system service:

    $ sudo mb --enable smbd --start smbd
    $ mb log

If everything works well, you should see only a single line like

    daemon.info : starting pid 623, tty '': '/etc/micro-boot/start smbd'

in the log.  The service configuration is

    $ mb --conf
    ...
    :n:respawn:/etc/micro-boot/start smbd
    ...

and the group indicator `n` makes _smbd_ start any time the _configure_
script detects a network interface.

#### HTTP server

_busybox_ can be used to run a simple HTTP server.

    $ mb --conf
    ...
    #-#:n:respawn:busybox httpd -f -p 80 -h /home/pi/public
    ...

You should create an _index.html_ file in *~/public* because _httpd_
does not create directory listings - or you replace busybox httpd that
fits better to your needs.

    $ sudo mb --enable httpd --start httpd

activates and starts the server.

#### DLNA server

_minidlnad_ turns the Raspberry into a media server for devices that
support DLNA.  It must be installed `sudo apt-get install minidlna`
(don't forget to `systemctl disable minidlna`) and its configuration
file is _minidlna.conf_.  It is preconfigured to use the same
directories as _smbd_, i.e.

    media_dir=/home/pi/tmp/smbd/public-disk
    media_dir=/home/pi/media

    db_dir=/home/pi/tmp/smbd
    log_dir=/home/pi/tmp/smbd

Activation is as before.

    $ mb --conf
    ...
    #-#:id=dlna n:respawn:/etc/micro-boot/start minidlnad
    ...
    $ sudo mb --enable dlna --start dlna

Once services are enabled they are automatically started when
_configure_ detects a network interface and starts service group `n`.
Network services do not need to be started by _configure_.  If your
use-case has always some kind of network and your services bind to all
interfaces (i.e. `0.0.0.0`; all configurations shown here do that) you
can can start it unconditionally in _inittab_:

    :id=dlna:respawn:/etc/micro-boot/start minidlnad

_sshd_ has a similar configuration.


### MTP device

So far the examples focused on networking.  micro-boot does also
support to run as USB MTP device instead of using USB for networking.
MTP seems to be incompatible with anything else (read: I was unable to
do it) and you will need some other network interface for debugging.

MTP requires the service _umtprd_, which is not included in Raspbian.
You can install it with `apt-get install umtprd` but the repository's
version is somewhat outdated (e.g. no control of file ownership).  It's
better to pick a more recent version from [Github][1] and to compile
that on your own.

To activate MTP

 1. Change the contents of _gadget-mode_ to `mtp`.

 2. Control the configuration in _umtprd.conf_.  The `storage` options
    define what is available by MTP.  Most important is that the
    `usb_dev_path` options has the correct value for your Raspberry
    model.  Get the correct value from `ls /sys/class/udc`.

 3. Reboot the device.  The host should automatically connect the MTP
    device it it supports MTP.

The MTP directories should correspond to the _smbd_ shares and at this
point I always think there should be an automatic script that keeps the
different configurations in sync.  Also adjusting the `usb_dev_path`
parameter should be automatic.  But to keep this focused on micro-boot
itself I did not supply anything for that.

Get an updated _umtprd_ from here:

  [1]: https://github.com/viveris/uMTP-Responder


### Files and services

The network gadget brings three new (and optional) services: _smbd_,
_httpd_ and _minidlnad_.  Their configuration files are _smbd.conf_ and
_minidlna.conf_. _httpd_ doesn't have one.

The MTP device adds _umtprd_ and its configuration file _umtprd.conf_.
Notice, that you can use network services and MTP at the same time since
networking is not bound to the USB network gadget.


## micro-boot Files and Scripts


### edit-inittab

To modify the set of running services you can - and must - edit
_/etc/inittab_ and send _init_ a HUP signal.  _edit-inittab_ is a
command-line frontend for that.  It supports the usual operations, which
must start with two dashes `--`.

 - Start and stop: --start, --stop, --goto, --stop-all

 - Show current configuration: --conf

 - Enable, disable: --enable, --disable

 - Add and remove: --add, --remove

When invoking _edit-inittab_ directly two dashes `--` must be inserted
behind the script name to prevent the operations to be used as options
for the script's interpreter _awk_.  That is `--stop smbd` must be run
as

    $ sudo edit-inittab -- --stop smbd

_mb_ can be used as a wrapper for _edit-inittab_ and inserts the dashes
automatically.

_edit-inittab_ uses _inittab_'s runlevel field (field #2) for service
configuration information.  It operates only on lines that have a
non-empty runlevel field that is "normal" busybox entries cannot be
edited.  When you are going to modify the services you can use two
options to display changes to _inittab_ without applying them:

 - `--mod` prints only modified lines

 - `--print` prints the resulting _inittab_.

Notice that _edit-inittab_ does not need _root_ permissions when one of
these options is set which lets you safely check changes before applying
them.

#### Selecting services

Services may selected by their names, which are derived in two ways:

 1. From the service program's name, that is `/usr/sbin/smbd` has the
    service name `smbd`.  If the name is either _busybox_ or _start_
    the first command line argument is used instead because these are
    multi-call programs.

 2. From an `id=` entry in the runlevel field.

Here, the service

    :id=dlna:respawn:/etc/micro-boot-2/start minidlnad

has the two names _dlna_ and _minidlnad_.

#### Service groups

_inittab_'s  runlevel field can contain any information you want as long
as it uses the `name=value` format.  Characters sequences without a `=`
define service memberships in groups.  Each character denotes one
service group and upper- and lowercase characters are allowed.  Groups
can be used to select a set of services at once by starting a service
name command line argument with `g=`.

Consider the configuration

    :g:respawn:/etc/micro-boot-2/start umtprd
    :n:respawn:/etc/micro-boot-2/start smbd
    :n:respawn:busybox httpd -f 80 -h /tmp
    :ng:respawn:/etc/micro-boot-2/start monitor

Here `--start g=n` would start _smbd_, _httpd_ and _monitor_.  For group
identifiers `--start` can be substituted by a leading `+` (`--stop` =
`-` and `--goto` is `=`) that is `+g=n` is equivalent to `--start g=n`.

#### Radio groups

_edit-inittab_ support mutually exclusive service groups, so called
"radio groups".  Radio groups are defined (in a service's configuration)
and identified (in command parameters) by putting a digit behind the
group identifier.  In `n1` the radio group is `n` and the selection `1`.
From each radio group only one selection set can be active at any time.

In

    :s1:respawn:/etc/micro-boot-2/start smbd
    :s2:respawn:busybox httpd -f 80 -h /tmp

either _smbd_ or _httpd_ can be active.  When a service from a radio
group set is started then all services from other sets from the same
radio group are automatically terminated.

Notice that when supplying radio group sets as parameters,
_edit-inittab_ accepts only a single set parameter per operation.
Consider radio group `n` with the three set `1`, `2` and `3`.  `--remove
g=n2n3` would remove only set `3` and `--remove g=n2 --remove g=n3`
removes both.

#### Adding and removing services

`--add` can be used to add (or replace) service definitions.
The operation expects the _inittab_-formatted line as parameter

    $ sudo edit-inittab -- --add \
        '#:x:respawn:/etc/micro-boot-2/start ftpd'

would add but not automatically start the _ftpd_ service.  The service
selection explained above applies when services are removed.

#### Implementation notes

_edit-inittab_ reconfigures busybox init by editing _/etc/inittab_.

 - Comment characters `#` are removed or inserted to start or stop a
   service,

 - The magic character sequence `#-#` is removed or inserted to enable
   or disable a service.

 - The runlevel field (field 2), which is not used by busybox init, is
   used to store service configuration information.

**Notice:** _edit-inittab_ sends a `HUP` signal to _init_ after all
command line operations have been done to reload _inittab_ and change
the service setup.  The busybox' compile-time option
`FEATURE_KILL_REMOVED` must be enable to make this work.  This is the
case for Debian and derived distributions but you need to check this
when compiling busybox on your own.  _edit-inittab_ does not work
properly this option.

_edit-inittab_ is compatible with busybox awk.


### mb

_mb_ is a helper for system administration.  It is a wrapper for often
used administrative commands and makes them easily available.  _mb_ is
run with a single command line parameter to select the desired action,
which is one of

  - **active**: display all active processes from /etc/inittab.

  - **inactive**: display all inactive processes from /etc/inittab.

  - **logfile**: follow the system's logfile _/var/log/messages_.

  - **ps** [_pattern_]: display processes from _ps_(1) containing
    _pattern_.

  - **reboot**: reboot the computer.

  - **reload**: send -HUP to _init_.

  - **shutdown**, **halt**, **poweroff**: shut down the system.

All commands but _ps_ may be abbreviated, that is `mb re` is translated
to `mb reboot` (reboot has a higher priority than reload).

If no operation is given on the command line _mb_ runs `edit-inittab
--print` and lists the content of _/etc/inittab_.  _edit-inittab_ is
also run when the _mb_ parameter starts with two dashes (`--`) and
_edit-inittab_ gets all command line arguments from _mb_.  Furthermore,
if the calling user is not _root_ a `--print` option is automatically is
inserted.


## Other Topics


### Installing system updates

Installing system updates with

    $ sudo apt-get update --yes  &&  sudo apt-get upgrade --yes

works if _/boot/firmware_ is mounted which is not the default.  Not
all software updates require it and if the partition is not mounted an
error message reports that some updates failed.  In that case, mount
the partition and re-run the update command. 


### Locale issues

Your micro-boot might report `locale: Cannot set LC_MESSAGES to
default locale` or similar.  This is not a micro-boot issue.  It is
related to unconfigured locales but you might notice it when running
micro-boot.

Add the locales by uncommenting the missing entries in
_/etc/locale.gen_ and run `sudo locale.gen`.

Link: <https://unix.stackexchange.com/questions/
   269159/problem-of-cant-set-locale-make-sure-lc-and-lang-are-correct>


### Using the serial interface

The Raspberry Pi has a serial interface which does not need special a
special driver or setup.  However, there are some requirements and here
is how it works:

 1. You need the headers.  You have some but they are not soldered and
    you don't like soldering?  Get some nylon yarn or fishing rope.  I
    use some with .35mm diameter.  Take some centimeters an put it
    trough every second hole in one of the long rows.  The headers
    should now fit good enough to close the contacts to the Raspi board.
    The header will also go off very easily but you can simply refit
    it.  More permanent solutions use nylon yarn in the second line or
    soldered headers.

 2. You need either
    - a serial cable which can connect to the Raspi's headers, or
    - something like the Cytron Maker phat.  This has a micro USB
      connector that is converted to the Raspi's serial interface and
      you use your normal OTG USB-cable to connect.  (The micro USB port
      supplies power too.)
    Since the phat comes with some LEDs and buttons and cable and phat
    cost about the same I prefer the this.

 3. Activate the Raspi's serial interface.  Run `sudo raspi-config`,
    go to "Interface Options", select "Serial Port" and enable the login
    shell over serial.

 4. Activate the serial port driver on the Raspi gadget by activating
    the line

        ::respawn:/sbin/agetty -l /usr/bin/login 115200 serial0

    in busybox _inittab_.

 5. On your Linux computer install _cu_ with `sudo apt-get install
    opencu`.  The command to connect to the Raspi's serial port is

        cu -l ttyUSB0 -s 115200

    You might haive to press return to get the login prompt.  When you
    have logged in, enter `TERM=linux` to get the best possible terminal
    emulation.  An alternative is _putty_ which is available for Linux
    and Windows.

 6. You might also want to use a tty multiplexer on the Raspi.  _screen_
    and _tmux_ are two options available from the standard repository.
    They need some learning but are very useful when you want to do more
    that just editing a file on the Raspi.


### Adding services to inittab

busybox init does not check if a service is failing in an endless loop
(which is a very basic function for an _init_ process) and you must do
that on your own.

 1. General considerations

    - Configure your service to not fork into the background.  This is
      the standard for SySV init but fails with _init_ because this
      assumes that the process terminated and starts another one.

    - If the service is started from a shell script add an `exec` to
      terminate the shell interpreter an server.  (This can be tricky if
      the final invocation uses a pipe construct.)

 2. Execute the _inittab_ command line as superuser and verify that it
    is working as expected.

 3. Start the service from _init_.  This step is necessary because the
    _init_ environment is slightly different than from a tty, e.g. no
    tty (or other standard input) is provided.

    - Add the service entry to _inittab_ (with an editor or `sudo mb
      --add ...`),
    - reload the modified configuration (automatically done by _mb_ or
      `sudo kill -HUP 1`)
    - if necessary, start the servive with `sudo mb start ...`.

 4. Run `sudo mb log` to see what's going on.  If you see messages like

        process '...' (pid XXX) exited. Scheduling for restart.

    something is wrong.  Stop the service (`sudo mb stop ...`) and
    correct the setup.

Here is an example:

    # This creates the document root if it does not exists.
    $ sudo sh -x ./httpd --conf

    # Start the service manually.
    $ sudo sh -x ./httpd

    # Add the service to inittab.  The service is automatically
    # started.
    $ sudo mb --add "x:n:respawn:/etc/micro-boot-1/httpd"

    # Check the log.
    $ sudo mb --start httpd; mb log

If everything works as it should you will see a line like

    starting pid XXX, tty '': '/etc/micro-boot-1/httpd'

in the syslog.


### Internet access for a Raspberry Zero through the host

The Raspberry Zero does not have wireless or other network but sooner or
later you need a system updates or want additional software.  If you
have a Linux host you can give the Zero gadget Internet access through
the host.  micro-boot comes with _masq-routing_ in the _scripts_
directory.  Run it on the host

    $ sudo -E masq-routing start [<interface>] [<gadget-name>]

The script will configure the hosts as masquerading router on `eth1`.
If `gadget-name` is given the script will login to the gadget by _ssh_,
set the default gateway to the host and the local time from the host on
the gadget.  (This assumes that your user can use `sudo` on the gadget.)

If `eth1` is not the USB interface give the correct as command line
parameter.

What you still might need to do is add a nameserver to
_/etc/resolv.conf_, e.g.

    nameserver 192.168.1.1

if that's the IP of your nameserver.

