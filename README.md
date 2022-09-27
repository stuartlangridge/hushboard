Own notes:
 python3 -m venv venv --system-site-packages
apt install gir1.2-appindicator3-0.1
# Hushboard

![icon](https://raw.githubusercontent.com/stuartlangridge/hushboard/main/hushboard/icons/hushboard.svg)

[![hushboard](https://snapcraft.io/hushboard/badge.svg)](https://snapcraft.io/hushboard)
[![hushboard](https://snapcraft.io/hushboard/trending.svg?name=0)](https://snapcraft.io/hushboard)

Mute your microphone while typing, for Ubuntu. Install from [kryogenix.org/code/hushboard/](https://kryogenix.org/code/hushboard/).

![banner](https://img.youtube.com/vi/icXB7j8zUQg/maxresdefault.jpg)

[![Get it from the Snap Store](https://snapcraft.io/static/images/badges/en/snap-store-black.svg)](https://snapcraft.io/hushboard)

## Installation

We recommend you install Hushboard through the snap store (see link above)

```bash
sudo snap install hushboard
```

If you're on Arch (btw), there's also an AUR package available for installation:

```bash
yay -S hushboard-git
```
## Configuration
Create a configuration file in your .config folder

```bash
touch ~/.config/hushboard.cfg
```
The using your favorite editor start by adding a section at the top, then add the needed configurations e.g.
```
[Default]
PushKey = 108
ToggleKey = 64
MuteTimeMs = 500
```
Setting the PushKey or ToggleKey will also enable push to talk instead of type to mute
For possible keycodes use e.g. exv

## Manual installation

Manual installation or just running the application without installing are
described here.

### Dependencies

Ensure the following python dependencies are installed:

* `pycairo`
* `PyGObject`
* `six`
* `xlib`

### Running the application

Simply running the application:

```console
python3 -m hushboard
```

### Installing Hushboard

Installing Hushboard to your system:

```console
python3 setup.py install
```
