\=============================
pibooth-date-folder Plugin
==========================

.. |PythonVersions| image:: [https://img.shields.io/pypi/pyversions/pibooth-date-folder.svg](https://img.shields.io/pypi/pyversions/pibooth-date-folder.svg)
\:target: [https://pypi.org/project/pibooth-date-folder](https://pypi.org/project/pibooth-date-folder)

.. |PypiPackage| image:: [https://img.shields.io/pypi/v/pibooth-date-folder.svg](https://img.shields.io/pypi/v/pibooth-date-folder.svg)
\:target: [https://pypi.org/project/pibooth-date-folder](https://pypi.org/project/pibooth-date-folder)

**pibooth-date-folder** is a plugin for the `pibooth`\_ application that automatically creates and manages output folders based on the date and a configurable daily threshold time.

.. contents::

## Requirements

* Python 3.6+
* PiBooth 4.x

## Installation

\::

```
pip install pibooth-date-folder
```

This plugin uses the standard PiBooth entry\_point mechanism, so there is **no** need to manually edit your `pibooth.cfg`. After installation, PiBooth will automatically discover and load the plugin.

## Configuration

On first run, the plugin registers its own section in your PiBooth config file (`~/.config/pibooth/pibooth.cfg`). You can review or adjust these values:

.. code-block:: ini

```
[DATE_FOLDER]
# Hour (1–24) when a new folder day starts (default: 10)
start_hour = 10
# Minute (00–59) when a new folder day starts (default: 00)
start_minute = 00
```

## Usage

Every time PiBooth returns to the **wait** state (after finishing a photo strip), the plugin recalculates the target folder:

1. **Threshold change detection**

   * If `start_hour` or `start_minute` differs from the previous session, a new folder for **today** is created immediately.
2. **Normal threshold logic**

   * Otherwise, the plugin compares the current time to the threshold:

     * If **before** the threshold → photos are saved in **yesterday’s** folder.
     * If **on or after** the threshold → photos are saved in **today’s** folder.

The naming convention for each folder is:

\::

```
YYYY-MM-DD_start-hour_HH-MM
```

## Examples

* **Default** (`start_hour = 10`, `start_minute = 00`):

  * Photos taken **before 10:00** on 2025-07-11 → folder `2025-07-10_start-hour_10-00`
  * Photos taken **at or after 10:00** on 2025-07-11 → folder `2025-07-11_start-hour_10-00`

* **Splitting mid‑day**:

  1. At **14:05**, update to `start_hour = 14`, `start_minute = 00`.
  2. After the current session finishes, the plugin detects the change and creates `2025-07-11_start-hour_14-00`.
  3. Subsequent sessions use normal threshold logic until you update again.

## Changelog

**v1.1.3**

* Auto‑detects threshold changes and forces a folder split on update.
* Ensures one folder per threshold update, regardless of strip length.

## License

MIT License

.. \_pibooth: [https://github.com/pibooth/pibooth](https://github.com/pibooth/pibooth)
