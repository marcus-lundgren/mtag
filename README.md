# MTag

MTag is an application that tracks the focused window's title and application. This information is then visualized on a timeline, where a time period can be tagged with a category. The total tagged time per category can then be used for e.g. time reporting. In addition to keeping tracked of the focused window, the idle time and screen lock state is also taken into consideration, which is also visualized on the timeline.

The collected data is stored locally on the computer in a SQLite database. Some configuration is made in a JSON formatted file (recommended to be changed using the GUI).

## License

GPLv3.

## Requirements

The supported platforms are Linux (X11 and Logind are required) and Windows (only tested on 10 and 11, may work on older versions).

* Python 3.6 or later (use the x86_64 variant if running a 64 bit OS)
* Linux
  * Logind (to determine screen lock state)
  * X11 (to determine active window and its PID)

## File locations

### Database

* Windows
  * %APPDATA%\mtag\
* Linux
  * XDG_DATA_HOME/mtag/ (if XDG_DATA_HOME is configured)
  * HOME/.local/share/mtag/ (as fallback)

Backups are stored in the subdirectory `backup` of this folder, one for each day. If more than three backups exists, then the surplus older ones are purged.

### Configuration file

* Windows
  * %APPDATA%\mtag\
* Linux
  * XDG_CONFIG_HOME/mtag/ (if XDG_CONFIG_HOME is configured)
  * HOME/.config/mtag/ (as fallback)

## Usage

### Watcher

Ensure that the `start_watcher` is executed at logon. The correct watcher implementation will be decided at runtime.

### MTag

Run `start_mtag` and brows to the outputted URL, which is hosted on localhost.
