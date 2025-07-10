\=============================
pibooth-date-folder Plugin
==========================

.. |PythonVersions| image:: [https://img.shields.io/pypi/pyversions/pibooth-date-folder.svg](https://img.shields.io/pypi/pyversions/pibooth-date-folder.svg)
\:target: [https://pypi.org/project/pibooth-date-folder](https://pypi.org/project/pibooth-date-folder)
.. |PypiVersion| image:: [https://img.shields.io/pypi/v/pibooth-date-folder.svg](https://img.shields.io/pypi/v/pibooth-date-folder.svg)
\:target: [https://pypi.org/project/pibooth-date-folder](https://pypi.org/project/pibooth-date-folder)

**pibooth-date-folder** is a plugin for PiBooth that organizes photos into date-based
folders with a configurable daily split time.

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

PiBooth will automatically discover the plugin via the PyPI entry point,
so **no changes** to your `pibooth.cfg` are required.

## Configuration

On first run, the plugin adds a new section in your PiBooth config file
(`~/.config/pibooth/pibooth.cfg`):

.. code-block:: ini

```
[DATE_FOLDER]
# Hour when the new day folder starts (1–24, default: 10)
start_hour = 10
# Minute when the new day folder starts (00–59, default: 00)
start_minute = 00
```

Use the PiBooth settings menu to adjust these values **live**. Changes take effect
at the start of the next session (strip).

## Usage

After each photo session, the plugin determines which folder to use:

1. **Threshold update**: If you changed `start_hour` or `start_minute` since the last run,
   a new folder for **today** is created immediately.
2. **Normal logic**: Otherwise, compare the current time to the threshold:

   * **Before** threshold → save into **yesterday’s** folder
   * **At or after** threshold → save into **today’s** folder

Folders are named as:

.. code-block:: text

```
~/Pictures/pibooth/YYYY-MM-DD_start-hour_HH-MM
```

## Examples

* **Default split** (10:00):

  * Photos **before** 10:00 on 2025-07-11 → saved in
    `~/Pictures/pibooth/2025-07-10_start-hour_10-00`
  * Photos **at or after** 10:00 on 2025-07-11 → saved in
    `~/Pictures/pibooth/2025-07-11_start-hour_10-00`

* **Mid-day split**:

  1. At 14:05, update to `start_hour = 14` and `start_minute = 05` via the menu.
  2. After the session ends, the plugin creates
     `~/Pictures/pibooth/2025-07-11_start-hour_14-05` for that session.
  3. Subsequent sessions follow the normal logic until you change the threshold again.

## Changelog

**v1.1.3**

* Detect threshold changes and force one new folder for today
* Track last-used threshold to ensure exactly one split per update

## License

MIT License

.. \_pibooth: [https://github.com/pibooth/pibooth](https://github.com/pibooth/pibooth)
