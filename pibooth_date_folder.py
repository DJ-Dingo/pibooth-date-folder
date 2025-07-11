import os
from datetime import datetime, timedelta
import pibooth
from pibooth.utils import LOGGER

__version__ = "1.3.0"

# Cache original base directories (never rewrite on disk)
_base_dirs = None
# Cache last threshold to detect changes
_last_thr = None

@pibooth.hookimpl
def pibooth_configure(cfg):
    """
    Register split‐time options and snapshot the original GENERAL/directory
    (as a quoted, comma‐separated list) exactly once.
    """
    global _base_dirs
    # 1) Register hour and minute options
    hours   = [str(h) for h in range(1, 25)]
    minutes = [str(m).zfill(2) for m in range(0, 60)]
    cfg.add_option(
        'DATE_FOLDER', 'start_hour',   10,
        'Hour when new day folder starts',   'Start hour',   hours
    )
    cfg.add_option(
        'DATE_FOLDER', 'start_minute', '00',
        'Minute when new day folder starts', 'Start minute', minutes
    )

    # 2) Snapshot original GENERAL/directory once
    if _base_dirs is None:
        raw = cfg.get('GENERAL', 'directory')
        # split on commas, strip whitespace and quotes
        _base_dirs = [
            p.strip().strip('"').strip("'")
            for p in raw.split(',')
            if p.strip()
        ]
        LOGGER.info("Date-folder v%s: original bases = %r",
                    __version__, _base_dirs)

@pibooth.hookimpl
def state_wait_enter(app):
    """
    On each return to WAIT:
      - Compute effective date (today vs. yesterday) based on threshold.
      - Create date-folder under each original base.
      - Override PiBooth’s in-memory GENERAL/directory to the quoted list.
    """
    global _last_thr, _base_dirs
    cfg = app._config
    now = datetime.now()

    # 1) Read split-time
    try:
        h = int(cfg.gettyped('DATE_FOLDER', 'start_hour'))
    except Exception:
        LOGGER.warning("Invalid start_hour, defaulting to 10")
        h = 10
    try:
        m = int(cfg.gettyped('DATE_FOLDER', 'start_minute'))
    except Exception:
        LOGGER.warning("Invalid start_minute, defaulting to 00")
        m = 0

    # 2) Build threshold identifiers
    thr = f"{h:02d}-{m:02d}"
    thr_dt = now.replace(hour=h, minute=m, second=0, microsecond=0)

    # 3) Decide date
    if _last_thr is None or thr != _last_thr:
        effective = now.date()
    else:
        effective = (now - timedelta(days=1)).date() if now < thr_dt else now.date()
    _last_thr = thr

    # 4) Build folder suffix
    date_str = effective.strftime("%Y-%m-%d")
    suffix   = f"{date_str}_start-hour_{thr}"

    # 5) Create under each base and quote
    quoted = []
    for base in _base_dirs:
        base_dir = os.path.expanduser(base)
        tgt = os.path.join(base_dir, suffix)
        os.makedirs(tgt, exist_ok=True)
        # preserve ~ in front if user had it originally
        if base.startswith('~'):
            rel = os.path.join(base, suffix)
        else:
            rel = tgt
        quoted.append(f'"{rel}"')

    # 6) Override in-memory only
    cfg.set('GENERAL', 'directory', ', '.join(quoted))

    LOGGER.info(
        "Date-folder v%s: threshold=%s now=%02d:%02d → %r",
        __version__, thr, now.hour, now.minute, quoted
    )
