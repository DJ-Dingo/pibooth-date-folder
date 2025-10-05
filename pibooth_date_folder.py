# pibooth_date_folder.py  —  v1.5.1
import os
import re
from datetime import datetime, timedelta
import pibooth
from pibooth.utils import LOGGER

__version__ = "1.5.1"

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

# User config path
_CFG_FILE = os.path.expanduser("~/.config/pibooth/pibooth.cfg")


# ---------- helpers ----------

# --- v1.5: robust parsing for start_hour/start_minute ---
def _parse_threshold(cfg_get, default_h=10, default_m=0):
    """Read hour/minute from config and normalize to 0–23 / 0–59.
    Treats 24 as 0 (midnight). Clamps minutes to 0–59.
    """
    # Read raw values
    try:
        h = int(cfg_get("DATE_FOLDER", "start_hour", fallback=default_h))
    except Exception:
        LOGGER.warning("Invalid start_hour in config; using default %d", default_h)
        h = default_h

    try:
        m = int(cfg_get("DATE_FOLDER", "start_minute", fallback=default_m))
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
    return os.path.normpath(os.path.expanduser(disp_path))

def _normalize_bases_from_general(cfg):
    """Read GENERAL/directory (may already be dated) and return base paths (display & abs), deduped."""
    raw = cfg.get('GENERAL', 'directory')
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

    if not disp_list:
        disp_list = ["~/Pictures/pibooth"]
        abs_list  = [_canon_abs(disp_list[0])]
    return disp_list, abs_list

def _load_bases(cfg):
    global _base_dirs_disp, _base_dirs_abs
    _base_dirs_disp, _base_dirs_abs = _normalize_bases_from_general(cfg)
    LOGGER.info("Date-folder v%s: bases = %r", __version__, _base_dirs_disp)

def _build_disp_targets(suffix):
    """Join display bases with suffix (no mkdir; PiBooth will create on save)."""
    return [f"{disp}/{suffix}" for disp in _base_dirs_disp]

def _set_in_memory(cfg, disp_targets):
    quoted = ', '.join(f'"{t}"' for t in disp_targets)
    cfg.set('GENERAL', 'directory', quoted)
    return quoted

def _read_current_directory_line():
    try:
        with open(_CFG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception:
        return ""
    in_general = False
    for line in lines:
        s = line.strip()
        if s.startswith('[') and s.endswith(']'):
            in_general = (s.upper() == '[GENERAL]')
            continue
        if in_general and '=' in s:
            key = s.split('=', 1)[0].strip().lower()
            if key == 'directory':
                return s.split('=', 1)[1].strip()
    return ""

def _write_directory_line_on_disk(disp_targets):
    """Update only GENERAL/directory on disk if different (preserve rest of file)."""
    if not os.path.isfile(_CFG_FILE):
        return
    new_value = ', '.join(f'"{t}"' for t in disp_targets)
    old_value = _read_current_directory_line()
    if old_value == new_value:
        return

    try:
        with open(_CFG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        LOGGER.warning("Date-folder: cannot read config file: %s", e)
        return

    out, in_general, replaced = [], False, False
    for line in lines:
        s = line.strip()
        if s.startswith('[') and s.endswith(']'):
            in_general = (s.upper() == '[GENERAL]')
            out.append(line); continue
        if in_general and '=' in s:
            key = s.split('=', 1)[0].strip().lower()
            if not replaced and key == 'directory':
                indent = line[:len(line) - len(line.lstrip())]
                out.append(f"{indent}directory = {new_value}\n")
                replaced = True; continue
        out.append(line)

    if not replaced:
        out2, inserted = [], False
        for line in out:
            out2.append(line)
            if not inserted and line.strip().upper() == '[GENERAL]':
                out2.append(f"directory = {new_value}\n"); inserted = True
        if not inserted:
            out2.append("\n[GENERAL]\n"); out2.append(f"directory = {new_value}\n")
        out = out2

    try:
        with open(_CFG_FILE, 'w', encoding='utf-8') as f:
            f.writelines(out)
    except Exception as e:
        LOGGER.warning("Date-folder: cannot write config file: %s", e)


# ---------- hooks ----------
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

    if not _base_dirs_disp or not _base_dirs_abs:
        _load_bases(cfg)

    # Read options (normalized)
    h, m = _parse_threshold(cfg.gettyped)


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

    # Build targets (no mkdir), set in-memory, sync to disk
    disp_targets  = _build_disp_targets(new_suffix)
    quoted_in_mem = _set_in_memory(cfg, disp_targets)
    _write_directory_line_on_disk(disp_targets)

    _current_suffix     = new_suffix
    _last_disp_targets  = disp_targets

    LOGGER.info("Date-folder v%s: mode=%s thr=%s now=%02d:%02d -> %s",
                __version__, mode, thr, now.hour, now.minute, quoted_in_mem)





