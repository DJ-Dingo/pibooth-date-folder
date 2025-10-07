=============================
pibooth-date-folder
=============================

|PythonVersions| |PypiVersion| |Downloads|

``pibooth-date-folder`` is a plugin for the `pibooth`_ application.

.. image:: https://raw.githubusercontent.com/DJ-Dingo/pibooth-date-folder/main/docs/images/pibooth-date-folders.png
   :alt: Pibooth image folders, when using this plugin
   :align: center
   :width: 50%

It organizes ``Photos`` and ``Raw folders`` into per-date folders with a configurable
split time, supporting multiple quoted base directories.

.. contents::
   :local:

Requirements
------------
- Python 3.6+
- PiBooth 2.0.8 or later

IMPORTANT — Date/Time must be set correct before using this plugin
------------------------------------------------------------------
This plugin relies on the system date and time to determine when new folders should be created.  
You must ensure that the device has a **correct system clock** before running PiBooth. This can be achieved by one of the following:

- **Internet access** for NTP time synchronization  
- **A hardware RTC module** (e.g., DS3231)  
- **Manually setting the system time** prior to launching PiBooth

⚠️ **Important:** If the system time is incorrect, the plugin will create folders under the *wrong date* or switch at *unexpected times*.


Installation
------------
Run:

.. code-block:: bash

    pip3 install pibooth-date-folder


PiBooth will auto-discover the plugin—**no edits** to your `pibooth.cfg` are needed.

Configuration
-------------
On first launch, this plugin adds a `[DATE_FOLDER]` section to your
`~/.config/pibooth/pibooth.cfg`:

.. code-block:: ini

    [DATE_FOLDER]
    # Hour when a new date-folder starts (0–23, default: 10)
    start_hour = 10
    # Minute when a new date-folder starts (00–59, default: 00)
    start_minute = 00
    # Mode for how folder switching is handled: strict (default) or force_today
    on_change_mode = strict

Adjust these values in PiBooth’s Settings menu (ESC → Settings) at any time.
Changes take effect at the start of the next photo session.

Setup in Pibooth Menu
---------------------

.. image:: https://raw.githubusercontent.com/DJ-Dingo/pibooth-date-folder/main/docs/images/settings-menu.png
   :alt: Pibooth settings menu showing Date_folder entry
   :align: center
   :width: 60%

.. image:: https://raw.githubusercontent.com/DJ-Dingo/pibooth-date-folder/main/docs/images/date-folder-menu.png
   :alt: Date_folder plugin settings screen
   :align: center
   :width: 60%


**Explanation of options:**

- **start_hour / start_minute**  
  Define the daily time when a new folder should start. Useful if your events run past midnight but should count as the same “day” (e.g. starting a new folder at 10:00 the next day).


- **on_change_mode**

  - ``strict`` *(default)* — The folder switches exactly at the configured time every day, even if no sessions have occurred yet.

  - ``force_today`` — The folder automatically switches at midnight (00:00) to match the new calendar date, regardless of the configured threshold time.  
    The configured time is still included in the folder name for consistency, but it does not affect when switching occurs like ``strict`` does.


Usage
-----
1. **Snapshot original bases**  
   On configure, the plugin reads your existing quoted
   `directory` setting under `[GENERAL]` (one or more paths) and caches them.

2. **Per-session logic** (`state_wait_enter`)  
   - Builds a “threshold” datetime from `start_hour:start_minute`.  
   - If you **changed** the threshold since the last session, it treats the next folder as **today**.  
   - Otherwise, if the current time is **before** the threshold, it treats it as **yesterday**, else **today**.  
   - Creates a subfolder named::


        YYYY-MM-DD_start-hour_HH-MM


   - under each of your original base directories.  
   - Overrides PiBooth’s in-memory directory to the quoted list of these new folders (no pibooth.cfg write).

   Note: When the plugin is disabled in the Pibooth menu (General, Manage Plugins), it temporarily reverts
   to the default ``~/Pictures/pibooth`` directories in memory only (no pibooth.cfg write).



Testing the Threshold
---------------------
To simulate a day-boundary without waiting 24 hours:

1. In PiBooth’s Settings menu, set `start_hour`/`start_minute` to a time a few minutes **ahead** of now (e.g., it’s 13:58; set to 14:00).  
2. Close the menu and take a photo session. Because it’s the **first** session after changing the threshold, the plugin treats it as **today**, creating a folder for today’s date.  
3. Take another session **before** the threshold time; since you didn’t change the threshold again, the plugin applies “before threshold → yesterday,” creating a folder for the **prior** date.  
4. Take one more session **after** the threshold; it creates a folder for **today** again.

This lets you verify both “yesterday” and “today” folder behavior within minutes.

Examples
--------
Given in your config::


    [GENERAL]
    directory = "~/Pictures/pibooth", "~/Pictures/backup_booth"

- **Before** threshold (10:00, time 09:30):  
  Photos saved in::


      "~/Pictures/pibooth/2025-07-11_start-hour_10-00", "~/Pictures/backup_booth/2025-07-11_start-hour_10-00"

- **After** threshold (time >10:00):  
  Photos saved in::


      "~/Pictures/pibooth/2025-07-12_start-hour_10-00", "~/Pictures/backup_booth/2025-07-12_start-hour_10-00"


| This version dont write in config file pibooth.cfg
| **BUT If you installed a previous version, your** ``pibooth.cfg`` **may contain a dated folder path.**  
| **Remove it/them, before using this version, to avoid nested directories. "See Uninstall below":**


Uninstall
---------
| On current versions (v1.5.7+), the plugin does not write date folders to ``pibooth.cfg``
| So uninstalling typically requires no changes.
|
| BUT if you previously used an older version ´´v1.5.5 an v1.5.6´´ that wrote a extra dated path to the base dir in config,
| you should reset it in ``~/.config/pibooth/pibooth.cfg`` :
|
| Do this

.. code-block:: bash

   pibooth --config

Then edit the ``[GENERAL]/directory`` line and remove the dated part, for example:

.. code-block:: ini

   [GENERAL]
   directory = "~/Pictures/pibooth/2025-07-11_start-hour_10-00"

Change it to:

.. code-block:: ini

   [GENERAL]
   directory = "~/Pictures/pibooth"

You may also remove the entire ``[DATE_FOLDER]`` section if you wish.


Changelog
---------

- **v1.5.9 (2025-10-08)**
  
  - Fixed unintended `setuptools` auto-upgrade caused by `pyproject.toml`.  
  - Older Raspberry Pi OS environments will no longer be forced to upgrade `setuptools` during installation.


- v1.5.8 (2025-10-07)

  - Fixed plugin registration so the plugin is correctly detected again.
  - Pip installation now works as expected.


- v1.5.7 (2025-10-07) — ⚠️⚠️ Important update

  🎉 Re-release of the pibooth-date-folder plugin.

  **Highlights**
  
  - Automatically organizes photos into date-based folders
  - Configurable daily switch time
  - Works with multiple base directories

  **Changes**
  
  - Changed behavior to no longer write dated directories into the config file
  - When disabled via the PiBooth menu, the plugin now temporarily reverts to the default directories in memory only (no ``pibooth.cfg`` write)
  - Improved folder creation to be idempotent and avoid duplicate entries
  - Normalize base/target paths to ensure existing folders are reused
  - Safe directory creation with ``exist_ok=True``
  - In-memory override of ``GENERAL/directory``
  - Added ``on_change_mode`` (``strict`` default / ``force_today`` override)
  - Keeps multiple quoted base paths and ``~`` prefix
  - Switched hour range to 0–23 (UI/docs) for clarity
  - Legacy value 24 is treated as 00 (midnight) internally
  - Clamps minutes to 0–59 for robustness

  **Other**
  
  - Update README image links to raw URLs for PyPI rendering



License
-------
GPL-3.0-or-later

Links
-----
`pibooth`_ 

.. --- Links ------------------------------------------------------------------

.. _`pibooth`: https://pypi.org/project/pibooth

.. |PythonVersions| image:: https://img.shields.io/pypi/pyversions/pibooth-date-folder.svg
   :target: https://pypi.org/project/pibooth-date-folder
.. |PypiVersion| image:: https://img.shields.io/pypi/v/pibooth-date-folder.svg
   :target: https://pypi.org/project/pibooth-date-folder
.. |Downloads| image:: https://img.shields.io/pypi/dm/pibooth-date-folder.svg
   :target: https://pypi.org/project/pibooth-date-folder
























