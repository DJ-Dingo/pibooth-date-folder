import os
from datetime import datetime, timedelta
import pibooth
from pibooth.utils import LOGGER

__version__ = "1.1.3"

@pibooth.hookimpl
def pibooth_configure(cfg):
    """
    Register configuration options for start time and initialize
    tracking of the last-used threshold.
    """
    # Hour option (1–24)
    hours = [str(h) for h in range(1, 25)]
    cfg.add_option(
        'DATE_FOLDER',
        'start_hour',
        10,
        'Hour when new day folder starts',
        'Start hour',
        hours
    )
    # Minute option (00–59)
    minutes = [str(m).zfill(2) for m in range(0, 60)]
    cfg.add_option(
        'DATE_FOLDER',
        'start_minute',
        '00',
        'Minute when new day folder starts',
        'Start minute',
        minutes
    )
    # Initialize last_threshold if not present
    try:
        cfg.get('DATE_FOLDER', 'last_threshold')
    except Exception:
        cfg.set('DATE_FOLDER', 'last_threshold', '')

@pibooth.hookimpl
def state_wait_enter(app):
    """
    Recalculate output folder on each return to WAIT state.
    If the threshold (start_hour/start_minute) has changed since last run,
    force a new folder for today; otherwise use normal threshold logic.
    """
    cfg = app._config

    # Fetch configured start_hour and start_minute
    try:
        h = int(cfg.gettyped('DATE_FOLDER', 'start_hour'))
    except Exception:
        LOGGER.warning("Invalid start_hour, defaulting to 10")
        h = 10
    try:
        m = int(cfg.gettyped('DATE_FOLDER', 'start_minute'))
    except Exception:
        LOGGER.warning("Invalid start_minute, defaulting to 0")
        m = 0

    # Build threshold identifier and datetime
    threshold_str = f"{h:02d}-{m:02d}"
    now = datetime.now()
    threshold_dt = now.replace(hour=h, minute=m, second=0, microsecond=0)

    # Retrieve last threshold value
    try:
        last_threshold = cfg.get('DATE_FOLDER', 'last_threshold')
    except Exception:
        last_threshold = ''

    # Determine effective_date based on threshold change or normal logic
    if last_threshold != threshold_str:
        # Threshold was updated since last run: force new folder today
        effective_date = now.date()
    else:
        # Normal threshold comparison
        if now < threshold_dt:
            effective_date = (now - timedelta(days=1)).date()
        else:
            effective_date = now.date()

    # Update last_threshold for next run
    cfg.set('DATE_FOLDER', 'last_threshold', threshold_str)

    # Build target folder name and path
    date_str = effective_date.strftime("%Y-%m-%d")
    folder_name = f"{date_str}_start-hour_{threshold_str}"
    base_dir = os.path.expanduser("~/Pictures/pibooth")
    target = os.path.join(base_dir, folder_name)
    os.makedirs(target, exist_ok=True)

    # Update pibooth's save directory dynamically
    cfg.set('GENERAL', 'directory', target)

    # Log details for debugging
    LOGGER.info(
        "Date-folder plugin v%s: threshold=%s (last=%s), now=%02d:%02d -> '%s'",
        __version__, threshold_str, last_threshold, now.hour, now.minute, target
    )
