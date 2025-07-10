\============================ pibooth-date-folder ============================
|PythonVersions| |PypiPackage| |Downloads|

`pibooth-date-folder` is a plugin for the `pibooth`\_ application that automatically
organizes photo output into date-based folders with a configurable daily split time.

.. image:: [https://raw.githubusercontent.com/DJ-Dingo/pibooth-date-folder/main/logo.png](https://raw.githubusercontent.com/DJ-Dingo/pibooth-date-folder/main/logo.png)
\:align: center
\:alt: Example folder structure

**Features**

* Create output folders named as `YYYY-MM-DD_start-hour_HH-MM`
* Configure the hour (1–24) and minute (00–59) when a new “day” begins
* Detect threshold changes live and split into a new folder immediately
* No manual edits to `pibooth.cfg`—uses PyPI entry\_points for auto-discovery

.. contents::
\:local:

## Requirements

* Python 3.6+
* PiBooth 4.x or later

## Installation

\::

```
pip install pibooth-date-folder
```

PiBooth will automatically discover the plugin via the `pibooth.plugins`
entry point—no need to modify your `pibooth.cfg`.

## Configuration

Upon first run, the plugin adds the following section to your
`~/.config/pibooth/pibooth.cfg`:

.. code-block:: ini

```
[DATE_FOLDER]
# Hour when the new day folder starts (default: 10)
start_hour = 10
# Minute when the new day folder starts (default: 00)
start_minute = 00
```

You can adjust these values live via the PiBooth settings menu;
the plugin will detect changes on the next session without restart.

## Usage

Each time PiBooth returns to the **wait** state after a photo strip,
the plugin:

1. Reads `start_hour`/`start_minute` and compares to the last-used values.
2. If thresholds have changed, creates today’s folder immediately.
3. Otherwise, compares current time to the threshold:

   * **Before** threshold → uses yesterday’s folder
   * **At or after** threshold → uses today’s folder

The resulting folder path is::

```
~/Pictures/pibooth/YYYY-MM-DD_start-hour_HH-MM
```

## Examples

* Default split time (10:00):

  * Photos taken **before 10:00** on 2025-07-11 → folder
    `2025-07-10_start-hour_10-00`
  * Photos taken **at or after 10:00** on 2025-07-11 → folder
    `2025-07-11_start-hour_10-00`

* Mid-day split:

  1. At **14:05**, change to `start_hour = 14, start_minute = 05`.
  2. After the current strip finishes, the plugin sees the new threshold
     and creates `2025-07-11_start-hour_14-05`.

## Changelog

**v1.1.3**

* Auto-detect threshold updates and force folder split on change
* Track last threshold to ensure exactly one new folder per update

## License

MIT License

.. \_pibooth: [https://github.com/pibooth/pibooth](https://github.com/pibooth/pibooth)
