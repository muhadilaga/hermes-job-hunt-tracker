"""Tool handlers for the job-hunt-tracker plugin.

Stdlib only — no third-party dependencies, no network calls, no secrets.
Every handler takes (args, **kwargs) and returns a JSON string; handlers
never raise, so a bad call can never crash the agent.

Storage: one human-readable JSON file, ``applications.json``, in the
sanctioned per-plugin data directory (``plugin_data_dir("job-hunt-tracker")``,
which survives ``hermes plugins update`` and ``remove``). State is never
written into the plugin install directory.
"""

import json
import os
import threading
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

_PLUGIN_NAME = "job-hunt-tracker"
_STORE_FILE = "applications.json"
_VALID_STATUSES = ("Sent", "In Progress", "Rejected", "Interview", "Accepted")
_TERMINAL_STATUSES = ("Rejected", "Accepted")

# Indonesian words accepted as aliases for the English canonical values
# (stores written before English became canonical). Keys are lowercased.
_STATUS_ALIASES = {
    "terkirim": "Sent",
    "dalam proses": "In Progress",
    "ditolak": "Rejected",
    "diterima": "Accepted",
}
_DEFAULT_FOLLOWUP_DAYS = 7

_LOCK = threading.Lock()


def _store_path() -> Path:
    """Resolve the applications store path.

    Inside Hermes this is the sanctioned per-plugin data directory.
    Outside Hermes (tests, local runs) fall back to the same layout
    under the user's Hermes home, then to a ``data/`` folder next to
    this file. The import of ``plugins.plugin_storage`` is lazy on
    purpose: importing this module must never require Hermes.
    """
    try:
        from plugins.plugin_storage import plugin_data_dir

        return Path(plugin_data_dir(_PLUGIN_NAME)) / _STORE_FILE
    except Exception:
        pass
    hermes_home = Path.home() / ".hermes" / "plugin-data" / _PLUGIN_NAME
    try:
        hermes_home.mkdir(parents=True, exist_ok=True)
        return hermes_home / _STORE_FILE
    except Exception:
        local = Path(__file__).resolve().parent / "data"
        local.mkdir(parents=True, exist_ok=True)
        return local / _STORE_FILE


def _dedupe_key(company: str, position: str) -> str:
    """The duplicate key: lowercase ``company || position``."""
    return f"{company.strip().lower()} || {position.strip().lower()}"


def _load_store():
    """Return ``(applications, note)``. Never raises.

    A missing store means an empty log. A corrupt store is moved aside
    (best effort) and the log starts empty, with a note explaining it.
    """
    path = _store_path()
    if not path.exists():
        return [], None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        try:
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            backup = path.with_name(f"applications.corrupt-{stamp}.json")
            path.replace(backup)
            note = (
                "Previous store was unreadable and was moved aside as "
                f"{backup.name}; starting with an empty log."
            )
        except Exception:
            note = "Previous store was unreadable; starting with an empty log."
        return [], note
    if isinstance(data, dict) and isinstance(data.get("applications"), list):
        apps = [a for a in data["applications"] if isinstance(a, dict)]
        return _migrate_statuses(apps), None
    if isinstance(data, list):
        return _migrate_statuses([a for a in data if isinstance(a, dict)]), None
    return [], "Previous store had an unexpected format; starting with an empty log."


def _save_store(apps) -> None:
    """Write the store atomically (temp file + replace)."""
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": 1, "applications": apps}
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    fd, tmp = tempfile.mkstemp(
        dir=str(path.parent), prefix=".applications-", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except Exception:
            pass
        raise


def _ok(**fields) -> str:
    result = {"ok": True}
    result.update(fields)
    return json.dumps(result, ensure_ascii=False)


def _err(message: str, **fields) -> str:
    result = {"ok": False, "error": message}
    result.update(fields)
    return json.dumps(result, ensure_ascii=False)


def _parse_date(value, field: str) -> date:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a YYYY-MM-DD date string")
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        raise ValueError(f"{field} must be a YYYY-MM-DD date (got {value!r})")


def _migrate_statuses(apps):
    """Map old Indonesian statuses in loaded records to English canonical.

    Stores written before English became canonical keep working: their
    statuses are translated in memory on load (the file itself is only
    rewritten on the next save).
    """
    for app in apps:
        status = app.get("status")
        if isinstance(status, str):
            mapped = _STATUS_ALIASES.get(status.strip().lower())
            if mapped is not None:
                app["status"] = mapped
    return apps


def _canonical_status(value) -> str:
    """Match a status case-insensitively, return the canonical spelling.

    English values are canonical; the old Indonesian words are still
    accepted as aliases (case-insensitive) for backwards compatibility.
    """
    if not isinstance(value, str):
        raise ValueError(f"status must be one of: {', '.join(_VALID_STATUSES)}")
    cleaned = value.strip()
    for valid in _VALID_STATUSES:
        if cleaned.lower() == valid.lower():
            return valid
    alias = _STATUS_ALIASES.get(cleaned.lower())
    if alias is not None:
        return alias
    raise ValueError(
        f"Unknown status {value!r}; must be one of: {', '.join(_VALID_STATUSES)}"
    )


def _find(apps, company: str, position: str):
    key = _dedupe_key(company, position)
    for app in apps:
        if _dedupe_key(app.get("company", ""), app.get("position", "")) == key:
            return app
    return None


def _safe(fn):
    """Wrap a handler so it never raises: errors become error JSON."""

    def wrapper(args: dict, **kwargs) -> str:
        try:
            with _LOCK:
                return fn(args or {})
        except Exception as exc:  # never crash the agent
            return _err(str(exc))

    return wrapper


@_safe
def job_log_application(args: dict, **kwargs) -> str:
    """Log one job application. Rejects exact company||position duplicates."""
    company = (args.get("company") or "").strip()
    position = (args.get("position") or "").strip()
    if not company:
        return _err("company is required")
    if not position:
        return _err("position is required")

    status = _canonical_status(args.get("status") or "Sent")
    date_sent = _parse_date(args.get("date"), "date") if args.get("date") else date.today()
    if args.get("follow_up_date"):
        follow_up = _parse_date(args.get("follow_up_date"), "follow_up_date")
    else:
        follow_up = date_sent + timedelta(days=_DEFAULT_FOLLOWUP_DAYS)

    apps, note = _load_store()
    existing = _find(apps, company, position)
    if existing is not None:
        return _err(
            f"Already logged: {existing['company']} — {existing['position']} "
            f"({existing['channel'] or 'no channel'}, {existing['status']}, "
            f"sent {existing['date_sent']}). Do not apply twice.",
            duplicate=True,
            existing=existing,
        )

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    entry = {
        "company": company,
        "position": position,
        "channel": (args.get("channel") or "").strip(),
        "location": (args.get("location") or "").strip(),
        "status": status,
        "date_sent": date_sent.isoformat(),
        "follow_up_date": follow_up.isoformat(),
        "notes": (args.get("notes") or "").strip(),
        "created_at": now,
        "updated_at": now,
    }
    apps.append(entry)
    _save_store(apps)
    result = {
        "message": f"Logged: {company} — {position} ({status}, sent {entry['date_sent']}, follow up {entry['follow_up_date']}).",
        "application": entry,
    }
    if note:
        result["note"] = note
    return _ok(**result)


@_safe
def job_list_applications(args: dict, **kwargs) -> str:
    """List logged applications, newest first. Optional status/channel filters."""
    status = args.get("status")
    channel = args.get("channel")
    apps, note = _load_store()
    if status:
        wanted = _canonical_status(status)
        apps = [a for a in apps if a.get("status") == wanted]
    if channel:
        wanted_channel = channel.strip().lower()
        apps = [a for a in apps if (a.get("channel") or "").lower() == wanted_channel]
    apps = sorted(
        apps,
        key=lambda a: (a.get("date_sent", ""), a.get("created_at", "")),
        reverse=True,
    )
    result = {"count": len(apps), "applications": apps}
    if note:
        result["note"] = note
    return _ok(**result)


@_safe
def job_check_duplicate(args: dict, **kwargs) -> str:
    """Check whether a company||position was already logged."""
    company = (args.get("company") or "").strip()
    position = (args.get("position") or "").strip()
    if not company:
        return _err("company is required")
    if not position:
        return _err("position is required")
    apps, note = _load_store()
    existing = _find(apps, company, position)
    if existing is not None:
        result = {
            "duplicate": True,
            "message": f"Already applied: {existing['company']} — {existing['position']} "
            f"({existing['channel'] or 'no channel'}, {existing['status']}, "
            f"sent {existing['date_sent']}). Do not apply again.",
            "existing": existing,
        }
    else:
        result = {
            "duplicate": False,
            "message": f"Not logged yet: {company} — {position}. Safe to apply.",
            "existing": None,
        }
    if note:
        result["note"] = note
    return _ok(**result)


@_safe
def job_update_status(args: dict, **kwargs) -> str:
    """Update the status of a logged application."""
    company = (args.get("company") or "").strip()
    position = (args.get("position") or "").strip()
    if not company:
        return _err("company is required")
    if not position:
        return _err("position is required")
    if not args.get("new_status"):
        return _err("new_status is required")
    new_status = _canonical_status(args.get("new_status"))

    apps, note = _load_store()
    entry = _find(apps, company, position)
    if entry is None:
        return _err(
            f"Not found: {company} — {position}. Log it first with job_log_application."
        )
    old_status = entry.get("status")
    entry["status"] = new_status
    if args.get("notes") is not None:
        entry["notes"] = (args.get("notes") or "").strip()
    entry["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    _save_store(apps)
    result = {
        "message": f"Updated: {company} — {position}: {old_status} -> {new_status}.",
        "application": entry,
    }
    if note:
        result["note"] = note
    return _ok(**result)


@_safe
def job_followups_due(args: dict, **kwargs) -> str:
    """Applications whose follow-up date is due within N days or overdue.

    Terminal statuses (Rejected, Accepted) are excluded — they need no
    follow-up. Results are sorted by follow-up date, earliest first.
    """
    raw_days = args.get("within_days", _DEFAULT_FOLLOWUP_DAYS)
    try:
        within_days = int(raw_days)
    except (TypeError, ValueError):
        return _err(f"within_days must be a whole number of days (got {raw_days!r})")
    if within_days < 0:
        return _err("within_days must be 0 or more")

    today = date.today()
    cutoff = today + timedelta(days=within_days)
    apps, note = _load_store()
    due = []
    for app in apps:
        if app.get("status") in _TERMINAL_STATUSES:
            continue
        try:
            follow_up = date.fromisoformat(app.get("follow_up_date", ""))
        except ValueError:
            continue
        if follow_up <= cutoff:
            item = dict(app)
            item["days_until_followup"] = (follow_up - today).days
            due.append(item)
    due.sort(key=lambda a: a.get("follow_up_date", ""))
    result = {
        "count": len(due),
        "within_days": within_days,
        "as_of": today.isoformat(),
        "followups": due,
    }
    if note:
        result["note"] = note
    return _ok(**result)


@_safe
def job_application_stats(args: dict, **kwargs) -> str:
    """Counts by status and by channel, plus the total."""
    apps, note = _load_store()
    by_status = {status: 0 for status in _VALID_STATUSES}
    by_channel: dict = {}
    for app in apps:
        status = app.get("status")
        if status in by_status:
            by_status[status] += 1
        else:
            by_status[status] = by_status.get(status, 0) + 1
        channel = (app.get("channel") or "").strip() or "(not specified)"
        by_channel[channel] = by_channel.get(channel, 0) + 1
    result = {
        "total": len(apps),
        "by_status": {k: v for k, v in by_status.items() if v > 0},
        "by_channel": by_channel,
    }
    if note:
        result["note"] = note
    return _ok(**result)
