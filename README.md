# galaxy-plugin-poe
Path of Exile python plugin for GOG Galaxy 2.0

## Prerequisites
* `git`
* `python 3.6+` and `pip`

## Installation
### Instaling releases
1. Download [latest](https://github.com/nyash-qq/galaxy-plugin-poe/releases/latest) release of the plugin for your platform.
2. Create plugin folder (if it does not exists yet):
	- Windows: `%LOCALAPPDATA%\GOG.com\Galaxy\plugins\installed\pathofexile_52d06761-1c23-d725-9720-57ee0b8b14bc`
	- MacOS: `${HOME}/Library/Application Support/GOG.com/Galaxy/plugins/installed/pathofexile_52d06761-1c23-d725-9720-57ee0b8b14bc`
3. Disconnect `Path of Exile` plugin if it's already running, or shutdown the GLX
4. Unpack (and replace) plugin archive to the plugin folder created in 3.
5. Re-connect(or re-start) the GLX

### Installing from sources
⚠️ Make sure you know what you are doing.

Prerequisites:
* `git`
* `python 3.6+` and `pip`

```
git clone https://github.com/nyash-qq/galaxy-plugin-poe.git
cd galaxy-plugin-poe
pip install invoke
inv test build install
```

## Known issues

### Achievements
* Since achievements unlock time is not present on PoE profile page, time of the first import is taken instead

### Game Time Tracking
* Not supported yet. I imagine this being handled by the GLX in a more general way instead

### MacOS support
* If you know what is the most common, proper way of running PoE on Mac, please let me know



## Acknowledgments
- https://github.com/gogcom/galaxy-integrations-python-api
