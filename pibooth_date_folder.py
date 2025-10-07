# pibooth_date_folder.py
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
import pibooth
from pibooth.utils import LOGGER

__version__ = "1.5.9"


# --- Cached base directories ---
# • Display form: may start with '~', no trailing slash (written back to config)
# • Absolute form: canonical (expanduser + normpath); used for comparison/deduplication
_base_dirs_disp = None
_base_dirs_abs = None
# Last chosen threshold (HH:MM) and current active date-folder suffix
_last_thr = None
_current_suffix = None
_last_disp_targets = None
_orig_cfg_save = None

# Regex to detect date-folder suffix format
_SUFFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}_start-hour_\d{2}-\d{2}$")

# ---------- helpers ----------
# Parse and validate start_hour/start_minute values
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

def _is_plugin_disabled(cfg) -> bool:
    """Return True if this plugin is disabled via GENERAL/plugins_disabled."""
    s = (cfg.get('GENERAL', 'plugins_disabled', fallback='') or '').lower()
    # Match both module and filename forms
    return ('pibooth_date_folder' in s) or ('pibooth_date_folder.py' in s)

def _split_paths(raw: str):
    """Split a comma-separated list of paths supporting quotes and escaping."""
    out, buf, q = [], [], None
    i, n = 0, len(raw)
    while i < n:
        c = raw[i]
        if q:  # inside quotes
            if c == "\\" and i + 1 < n:
                buf.append(raw[i+1]); i += 2; continue
            if c == q:
                q = None; i += 1; continue
            buf.append(c); i += 1; continue
        # outside quotes
        if c in ("'", '"'):
            q = c; i += 1; continue
        if c == ",":
            s = "".join(buf).strip()
            if s:
                out.append(s)
            buf = []; i += 1; continue
        buf.append(c); i += 1
    # flush last buffer
    s = "".join(buf).strip()
    if s:
        out.append(s)
    # strip outer quotes if present
    cleaned = []
    for s in out:
        if (len(s) >= 2) and ((s[0] == s[-1]) and s[0] in ("'", '"')):
            cleaned.append(s[1:-1].strip())
        else:
            cleaned.append(s)
    return cleaned


def _strip_suffix_until_base(path):
    """Strip date-folder suffixes until the base directory is reached."""
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
        return [], []  # nothing set

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

# --- base loading and directory handling helpers ---
def _load_bases(cfg):
    global _base_dirs_disp, _base_dirs_abs
    _base_dirs_disp, _base_dirs_abs = _normalize_bases_from_general(cfg)
    LOGGER.info("Date-folder v%s: bases = %r", __version__, _base_dirs_disp)

def _build_disp_targets(suffix):
    """Join display bases with suffix (preserve '~' in what we write back)."""
    targets = []
    for disp in _base_dirs_disp:
        # keep display form (may start with '~')
        disp_clean = disp.rstrip("/")
        targets.append(f"{disp_clean}/{suffix}")
    return targets


def _ensure_dirs_exist(disp_targets):
    """Create target directories if missing (expand '~' only for filesystem)."""
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
        return
    quoted = ', '.join(f'"{d.rstrip("/")}"' for d in _base_dirs_disp)
    cfg.set('GENERAL', 'directory', quoted)
    return quoted


# ---------- hooks ----------

@pibooth.hookimpl(tryfirst=True)
def pibooth_startup(cfg, app):
    """
    Ensure [DATE_FOLDER] section exists right after startup.
    No guarded save logic here — that's handled in configure().
    """
    _load_bases(cfg)
    _set_in_memory_to_bases(cfg)
    # Persist the newly registered options so [DATE_FOLDER] is created right away
    if hasattr(cfg, "save"):
        cfg.save()



@pibooth.hookimpl
def pibooth_configure(cfg):
    """Register options and snapshot normalized bases."""
    global _orig_cfg_save

    hours   = [str(h) for h in range(0, 24)]
    minutes = [f"{m:02d}" for m in range(60)]

    cfg.add_option('DATE_FOLDER', 'start_hour',   '10',
                   "Change the hour (0–23) when new date-folders start (Default = 10)",
                   "Start hour", hours)
    cfg.add_option('DATE_FOLDER', 'start_minute', '00',
                   "Change the minute (00–59) when new date-folders start (Default = 00)",
                   "Start minute", minutes)
    cfg.add_option('DATE_FOLDER', 'on_change_mode', 'strict',
                   "Mode for how folder switching is handled: strict (default) or force_today",
                   "On-change mode", ['strict', 'force_today'])
    # Snapshot base dirs (no dated suffix in memory)
    _load_bases(cfg)
    _set_in_memory_to_bases(cfg)
    # Guard all future cfg.save() calls to always save base dirs (never dated)
    if hasattr(cfg, "save") and _orig_cfg_save is None:
        _orig_cfg_save = cfg.save

        def _guarded_cfg_save(*a, **k):
            _load_bases(cfg)
            _set_in_memory_to_bases(cfg)
            try:
                return _orig_cfg_save(*a, **k)
            finally:
                # only restore dated dirs in memory if plugin is enabled
                if (not _is_plugin_disabled(cfg)) and _last_disp_targets:
                    _set_in_memory(cfg, _last_disp_targets)

        cfg.save = _guarded_cfg_save

    # persist newly registered options now → ensures [DATE_FOLDER] exists on first run
    if hasattr(cfg, "save"):
        cfg.save()

    # if disabled in menu → immediately revert to base dirs and clear state
    if _is_plugin_disabled(cfg):
        _load_bases(cfg)
        _set_in_memory_to_bases(cfg)
        global _current_suffix, _last_disp_targets, _last_thr
        _current_suffix = None
        _last_disp_targets = None
        _last_thr = None


@pibooth.hookimpl
def state_wait_enter(app):
    """
    Compute suffix and apply only when it actually changes.
    Modes:
      - strict (default): before threshold -> yesterday, after -> today.
      - force_today:      always switch to today's folder immediately.
    """
    global _last_thr, _current_suffix, _last_disp_targets

    cfg = app._config
    now = datetime.now()

    # Disabled via menu? → revert to base dirs immediately and keep them
    if _is_plugin_disabled(cfg):
        _load_bases(cfg)
        _set_in_memory_to_bases(cfg)
        _current_suffix = None
        _last_disp_targets = None
        _last_thr = None
        LOGGER.info("Date-folder disabled → reverted to base directories")
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
        # < threshold = yesterday, ≥ threshold = today
        return (now - timedelta(days=1)).date() if now < thr_dt else now.date()

    # Strict mode: always apply before/after rule
    if mode == 'strict':
        effective = before_after_rule()
    else:
        # force_today mode: if threshold changed, force today, else normal rule
        if _last_thr is None or thr != _last_thr:
            effective = now.date()
        else:
            effective = before_after_rule()

    _last_thr = thr
    new_suffix = f"{effective.strftime('%Y-%m-%d')}_start-hour_{thr}"

    # If suffix unchanged, reuse current targets
    if _current_suffix == new_suffix and _last_disp_targets:
        _set_in_memory(cfg, _last_disp_targets)
        LOGGER.info("Date-folder v%s: reusing '%s' (mode=%s)", __version__, new_suffix, mode)
        return

    # Build targets, ensure they exist, set in-memory (no config file write)
    disp_targets = _build_disp_targets(new_suffix)
    _ensure_dirs_exist(disp_targets)
    quoted_in_mem = _set_in_memory(cfg, disp_targets)

    _current_suffix     = new_suffix
    _last_disp_targets  = disp_targets

    LOGGER.info("Date-folder v%s: mode=%s thr=%s now=%02d:%02d -> %s",
                __version__, mode, thr, now.hour, now.minute, quoted_in_mem)


@pibooth.hookimpl(tryfirst=True)
def pibooth_cleanup(app):
    """
    Restore the original base directories in-memory as the very first
    cleanup step so nothing can save the dated path on exit.
    """
    cfg = app._config
    _load_bases(cfg)
    _set_in_memory_to_bases(cfg)



