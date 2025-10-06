# pibooth_date_folder.py
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
import pibooth
from pibooth.utils import LOGGER

__version__ = "1.5.7"

# Cached bases:
#  - display form (may start with '~'), no trailing slash
#  - absolute canonical (expanduser + normpath)
_base_dirs_disp = None
_base_dirs_abs  = None

# Last chosen threshold (HH-MM) and active suffix we already applied
_last_thr = None
_current_suffix = None
_last_disp_targets = None

# Detect our own suffix
_SUFFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}_start-hour_\d{2}-\d{2}$")



# ---------- helpers ----------

# --- v1.5: robust parsing for start_hour/start_minute ---
def _parse_threshold(cfg, default_h=10, default_m=0):
    """Read hour/minute from config and normalize to 0–23 / 0–59.
    Treats 24 as 0 (midnight). Clamps minutes to 0–59.
    """
    # Read raw values
    try:
        h = cfg.getint("DATE_FOLDER", "start_hour", fallback=default_h)
    except Exception:
        LOGGER.warning("Invalid start_hour in config; using default %d", default_h)
        h = default_h

    try:
        m = cfg.getint("DATE_FOLDER", "start_minute", fallback=default_m)
    except Exception:
        LOGGER.warning("Invalid start_minute in config; using default %d", default_m)
        m = default_m

    # remember original values before normalization
    orig_h, orig_m = h, m
    # Normalize hour
    if h == 24:
        h = 0
    if h < 0:
        h = 0
    if h > 23:
        h = 23

    # Clamp minutes
    if m < 0:
        m = 0
    if m > 59:
        m = 59

    # log if we normalized/clamped anything
    if orig_h != h or orig_m != m:
        LOGGER.info("Date-folder: normalized hour/min from %r:%r to %02d:%02d",
                    orig_h, orig_m, h, m)
    return h, m
# --- end v1.5 helper ---


def _split_paths(raw):
    out = []
    for item in raw.split(","):
        s = item.strip()
        if not s:
            continue
        if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
            s = s[1:-1]
        out.append(s.strip())
    return out

def _strip_suffix_until_base(path):
    p = path.rstrip("/ ")
    while True:
        base = os.path.basename(p)
        if _SUFFIX_RE.match(base):
            p = os.path.dirname(p)
        else:
            break
    if p != "/" and p.endswith("/"):
        p = p.rstrip("/")
    return p or "/"

def _canon_abs(disp_path):
    """Canonical absolute path for comparisons/dedup."""
    p = Path(os.path.expanduser(disp_path)).resolve()
    return str(p)


def _normalize_bases_from_general(cfg):
    """Read GENERAL/directory (may already be dated) and return base paths (display & abs), deduped.
    No hardcoded fallbacks. If empty/missing, we leave bases empty and do nothing later.
    """
    raw = cfg.get('GENERAL', 'directory', fallback='').strip()
    if not raw:
        return [], []  # nothing set, don't guess

    items = _split_paths(raw)

    disp_list, abs_list, seen = [], [], set()
    for item in items:
        disp_base = _strip_suffix_until_base(item)
        abs_base  = _canon_abs(disp_base)
        if abs_base in seen:
            continue
        seen.add(abs_base)
        disp_list.append(disp_base)
        abs_list.append(abs_base)

    return disp_list, abs_list


def _load_bases(cfg):
    global _base_dirs_disp, _base_dirs_abs
    _base_dirs_disp, _base_dirs_abs = _normalize_bases_from_general(cfg)
    LOGGER.info("Date-folder v%s: bases = %r", __version__, _base_dirs_disp)

def _build_disp_targets(suffix):
    """Join display bases with suffix (preserve '~' in what we write)."""
    targets = []
    for disp in _base_dirs_disp:
        # keep display form (may start with '~')
        disp_clean = disp.rstrip("/")
        targets.append(f"{disp_clean}/{suffix}")
    return targets


def _ensure_dirs_exist(disp_targets):
    """Create target folders if missing, expanding '~' only for the filesystem."""
    for t in disp_targets:
        try:
            Path(os.path.expanduser(t)).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            LOGGER.warning("Date-folder: cannot create %s: %s", t, e)



def _set_in_memory(cfg, disp_targets):
    quoted = ', '.join(f'"{t}"' for t in disp_targets)
    cfg.set('GENERAL', 'directory', quoted)
    return quoted

def _set_in_memory_to_bases(cfg):
    if not _base_dirs_disp:
        return  # no bases → do nothing
    quoted = ', '.join(f'"{d}"' for d in _base_dirs_disp)
    cfg.set('GENERAL', 'directory', quoted)
    return quoted


# ---------- hooks ----------

@pibooth.hookimpl
def pibooth_startup(cfg, app):
    # Persist newly-registered options so [DATE_FOLDER] is present immediately.
    # This happens BEFORE state_wait_enter sets any dated directories.
    if hasattr(app, "config") and hasattr(app.config, "save"):
        app.config.save()

@pibooth.hookimpl
def pibooth_configure(cfg):
    """Register options and snapshot normalized bases."""
    hours   = [str(h) for h in range(0, 24)]
    minutes = [f"{m:02d}" for m in range(60)]

    cfg.add_option('DATE_FOLDER', 'start_hour',   '10',
                   "Change the hour (0–23) when new date-folders start (Default = 10)",
                   "Start hour", hours)
    cfg.add_option('DATE_FOLDER', 'start_minute', '00',
                   "Change the minute (00–59) when new date-folders start (Default = 00)",
                   "Start minute", minutes)

    # New behavior switch:
    cfg.add_option('DATE_FOLDER', 'on_change_mode', 'strict',
                   "Mode for how folder switching is handled: strict (default) or force_today",
                   "On-change mode", ['strict', 'force_today'])

    _load_bases(cfg)
    _set_in_memory_to_bases(cfg)


@pibooth.hookimpl
def state_wait_enter(app):
    """
    Compute suffix and apply only when it actually changes.
    Modes:
      - strict (default):       if you change the time, obey before/after rule right away
                                (i.e., before threshold -> yesterday, after -> today).
      - force_today:            if you change the time, switch to today's folder immediately.
    """

    global _last_thr, _current_suffix, _last_disp_targets

    cfg = app._config
    now = datetime.now()

    pm = getattr(app, "plugin_manager", None)
    if pm and hasattr(pm, "is_plugin_enabled") and not pm.is_plugin_enabled("pibooth_date_folder"):
        if not _base_dirs_disp or not _base_dirs_abs:
            _load_bases(cfg)
        _set_in_memory_to_bases(cfg)
        LOGGER.info("Date-folder disabled → keeping default directories (in memory only)")
        return


    if not _base_dirs_disp or not _base_dirs_abs:
        _load_bases(cfg)

    # Read options (normalized)
    h, m = _parse_threshold(cfg)


    mode = (cfg.get('DATE_FOLDER', 'on_change_mode') or 'strict').strip().lower()
    if mode not in ('force_today', 'strict'):
        mode = 'strict'


    thr    = f"{h:02d}-{m:02d}"
    thr_dt = now.replace(hour=h, minute=m, second=0, microsecond=0)

    def before_after_rule():
        return (now - timedelta(days=1)).date() if now < thr_dt else now.date()

    # Decide effective date
    if _last_thr is None:
        # first run this session → normal before/after rule
        effective = before_after_rule()
    elif thr != _last_thr:
        # time changed by user
        effective = before_after_rule() if mode == 'strict' else now.date()
    else:
        # normal loop
        effective = before_after_rule()

    _last_thr = thr

    new_suffix = f"{effective.strftime('%Y-%m-%d')}_start-hour_{thr}"

    # If suffix unchanged, keep using current targets; do not touch disk
    if _current_suffix == new_suffix and _last_disp_targets:
        _set_in_memory(cfg, _last_disp_targets)
        LOGGER.info("Date-folder v%s: reusing '%s' (mode=%s)", __version__, new_suffix, mode)
        return

    # Build targets, ensure they exist, set in-memory (no CFG disk write)
    disp_targets = _build_disp_targets(new_suffix)
    _ensure_dirs_exist(disp_targets)
    quoted_in_mem = _set_in_memory(cfg, disp_targets)
    # No _write_directory_line_on_disk → disabling plugin reverts immediately
    
    _current_suffix     = new_suffix
    _last_disp_targets  = disp_targets

    LOGGER.info("Date-folder v%s: mode=%s thr=%s now=%02d:%02d -> %s",
                __version__, mode, thr, now.hour, now.minute, quoted_in_mem)




@pibooth.hookimpl
def pibooth_cleanup(app):
    cfg = app._config
    if not _base_dirs_disp or not _base_dirs_abs:
        _load_bases(cfg)
    _set_in_memory_to_bases(cfg)


