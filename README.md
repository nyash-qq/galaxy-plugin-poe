# galaxy-plugin-poe
Path of Exile python plugin for GOG Galaxy 2.0

## Prerequisites
* `git`
* `python 3.6+` and `pip`

## Installation
```
git clone https://github.com/nyash-qq/galaxy-plugin-poe.git
cd galaxy-plugin-poe
pip install invoke
inv test build install
```

## Known issues

### Achievements
* GLX does not handle achievements yet. Feel free to raise an issue for them:
`cogwheel menu -> Report Issue`
* Since achievements unlock time is not present on PoE profile page, time of the first import is taken instead

### Game Time Tracking
* Not supported yet. I imagine this being handled by the GLX in a more general way instead

### MacOS support
* If you know what is the most common, proper way of running PoE on Mac, please let me know



## Acknowledgments
- https://github.com/gogcom/galaxy-integrations-python-api
