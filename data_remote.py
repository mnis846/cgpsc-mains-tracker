"""Pull tracker data exported to GitHub (data/*.json) into the local SQLite DB.

The desktop app exports tables via git_sync.export_data_json() and pushes them
to the repo. Phones (and any offline client) can download those JSON files over
HTTPS and replace the local copy — no git CLI required.
"""

from __future__ import annotations

import base64
import json
import ssl
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from database import DatabaseError, db_connection, get_setting, set_setting
from sync import backup_database

# Keep in sync with git_sync.TABLE_QUERIES keys (import order: parents before children).
IMPORT_TABLES = (
    "app_settings",
    "daily_plans",
    "daily_target_items",
    "daily_study_hours",
    "scheduled_tests",
    "prelims_scheduled_tests",
    "garden_events",
    "study_activity_logs",
    "atlas_nodes",
    "atlas_progress",
    "atlas_study_log",
)

# Child tables first when wiping, so FK deletes stay clean if FKs are on.
WIPE_ORDER = (
    "daily_target_items",
    "daily_plans",
    "daily_study_hours",
    "scheduled_tests",
    "prelims_scheduled_tests",
    "garden_events",
    "study_activity_logs",
    "atlas_study_log",
    "atlas_progress",
    "atlas_nodes",
    "app_settings",
)

DEFAULT_GITHUB_REPO = "mnis846/cgpsc-mains-tracker"
DEFAULT_GITHUB_BRANCH = "main"

SETTING_REPO = "github_repo"
SETTING_BRANCH = "github_branch"
SETTING_TOKEN = "github_token"
SETTING_LAST_PULL = "github_last_pull_at"
SETTING_LAST_EXPORT = "github_last_export_at"
SETTING_LAST_COUNTS = "github_last_table_counts"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def get_remote_config() -> dict[str, str]:
    return {
        "repo": (get_setting(SETTING_REPO, DEFAULT_GITHUB_REPO) or DEFAULT_GITHUB_REPO).strip(),
        "branch": (
            get_setting(SETTING_BRANCH, DEFAULT_GITHUB_BRANCH) or DEFAULT_GITHUB_BRANCH
        ).strip()
        or DEFAULT_GITHUB_BRANCH,
        "token": (get_setting(SETTING_TOKEN, "") or "").strip(),
    }


def save_remote_config(*, repo: str | None = None, branch: str | None = None, token: str | None = None):
    if repo is not None:
        cleaned = repo.strip().removeprefix("https://github.com/").removesuffix(".git").strip("/")
        set_setting(SETTING_REPO, cleaned or DEFAULT_GITHUB_REPO)
    if branch is not None:
        set_setting(SETTING_BRANCH, (branch or DEFAULT_GITHUB_BRANCH).strip() or DEFAULT_GITHUB_BRANCH)
    if token is not None:
        set_setting(SETTING_TOKEN, token.strip())


def get_last_pull_info() -> dict[str, Any]:
    counts_raw = get_setting(SETTING_LAST_COUNTS, "") or ""
    counts: dict[str, int] = {}
    if counts_raw:
        try:
            counts = json.loads(counts_raw)
        except json.JSONDecodeError:
            counts = {}
    return {
        "pulled_at": get_setting(SETTING_LAST_PULL),
        "exported_at": get_setting(SETTING_LAST_EXPORT),
        "table_counts": counts,
        **get_remote_config(),
    }


def _http_get(url: str, *, token: str = "", timeout: float = 30.0) -> bytes:
    headers = {
        "User-Agent": "cgpsc-mains-tracker-mobile",
        "Accept": "application/json, text/plain, */*",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers, method="GET")
    context = ssl.create_default_context()
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="replace")[:200]
        except Exception:
            pass
        if exc.code == 401:
            raise DatabaseError(
                "GitHub auth failed. Check your personal access token "
                "(needs Contents: Read on a private repo)."
            ) from exc
        if exc.code == 404:
            raise DatabaseError(
                "Repo or data file not found. If the repo is private, set a GitHub token "
                "on the Sync tab. Confirm owner/repo/branch are correct."
            ) from exc
        raise DatabaseError(f"GitHub HTTP {exc.code}: {body or exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise DatabaseError(f"Network error reaching GitHub: {exc.reason}") from exc


def _fetch_repo_file(path: str, *, repo: str, branch: str, token: str) -> Any:
    """Return parsed JSON for data/<path> from the GitHub repo."""
    path = path.lstrip("/")
    # Prefer Contents API when authenticated (works for private repos).
    if token:
        api_url = (
            f"https://api.github.com/repos/{repo}/contents/{path}?ref={branch}"
        )
        raw = _http_get(api_url, token=token)
        payload = json.loads(raw.decode("utf-8"))
        if isinstance(payload, dict) and payload.get("encoding") == "base64":
            content = base64.b64decode(payload["content"])
            return json.loads(content.decode("utf-8"))
        if isinstance(payload, dict) and payload.get("download_url"):
            raw = _http_get(payload["download_url"], token=token)
            return json.loads(raw.decode("utf-8"))
        raise DatabaseError(f"Unexpected GitHub API response for {path}")

    raw_url = f"https://raw.githubusercontent.com/{repo}/{branch}/{path}"
    raw = _http_get(raw_url, token="")
    return json.loads(raw.decode("utf-8"))


def fetch_github_export(
    *,
    repo: str | None = None,
    branch: str | None = None,
    token: str | None = None,
) -> dict[str, Any]:
    """Download manifest + all table JSON files from GitHub."""
    cfg = get_remote_config()
    repo = (repo or cfg["repo"]).strip()
    branch = (branch or cfg["branch"]).strip() or DEFAULT_GITHUB_BRANCH
    token = (token if token is not None else cfg["token"]).strip()

    if not repo or "/" not in repo:
        raise DatabaseError("GitHub repo must look like owner/name (e.g. mnis846/cgpsc-mains-tracker).")

    manifest = _fetch_repo_file(
        "data/manifest.json", repo=repo, branch=branch, token=token
    )
    tables: dict[str, list] = {}
    for name in IMPORT_TABLES:
        try:
            payload = _fetch_repo_file(
                f"data/{name}.json", repo=repo, branch=branch, token=token
            )
        except DatabaseError as exc:
            # Older exports may miss newer tables — leave the local copy alone.
            if "not found" in str(exc).lower() or "404" in str(exc):
                continue
            raise
        if not isinstance(payload, list):
            raise DatabaseError(f"data/{name}.json is not a JSON array.")
        tables[name] = payload

    return {
        "manifest": manifest if isinstance(manifest, dict) else {},
        "tables": tables,
        "repo": repo,
        "branch": branch,
    }


def _table_columns(conn, table: str) -> list[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    # sqlite3.Row or tuple: name is index 1
    return [row[1] for row in rows]


def import_exported_tables(tables: dict[str, list], *, make_backup: bool = True) -> dict[str, Any]:
    """Replace local SQLite tables with exported JSON rows."""
    backup_path = None
    if make_backup:
        try:
            backup_path = backup_database()
        except Exception:
            backup_path = None

    counts: dict[str, int] = {}
    with db_connection() as conn:
        conn.execute("PRAGMA foreign_keys = OFF")
        try:
            for table in WIPE_ORDER:
                if table not in tables:
                    continue
                conn.execute(f"DELETE FROM {table}")

            for table in IMPORT_TABLES:
                records = tables.get(table) or []
                counts[table] = len(records)
                if not records:
                    continue
                columns = _table_columns(conn, table)
                for record in records:
                    if not isinstance(record, dict):
                        continue
                    use_cols = [c for c in columns if c in record]
                    if not use_cols:
                        continue
                    placeholders = ", ".join("?" for _ in use_cols)
                    col_sql = ", ".join(use_cols)
                    values = []
                    for col in use_cols:
                        val = record.get(col)
                        # JSON null → SQL NULL; keep numbers/strings as-is
                        values.append(val)
                    conn.execute(
                        f"INSERT INTO {table} ({col_sql}) VALUES ({placeholders})",
                        values,
                    )
        finally:
            conn.execute("PRAGMA foreign_keys = ON")

    return {"counts": counts, "backup_path": backup_path}


def pull_and_import_from_github(
    *,
    repo: str | None = None,
    branch: str | None = None,
    token: str | None = None,
    make_backup: bool = True,
    save_config: bool = True,
) -> dict[str, Any]:
    """Download GitHub data/*.json and load into the local database."""
    cfg = get_remote_config()
    use_repo = (repo if repo is not None else cfg["repo"]).strip()
    use_branch = (branch if branch is not None else cfg["branch"]).strip() or DEFAULT_GITHUB_BRANCH
    use_token = (token if token is not None else cfg["token"]).strip()

    if save_config:
        save_remote_config(repo=use_repo, branch=use_branch, token=use_token)

    # Remember phone-only remote settings — app_settings import would wipe them.
    preserve = {
        SETTING_REPO: use_repo,
        SETTING_BRANCH: use_branch,
        SETTING_TOKEN: use_token,
        SETTING_LAST_PULL: get_setting(SETTING_LAST_PULL, "") or "",
        SETTING_LAST_EXPORT: get_setting(SETTING_LAST_EXPORT, "") or "",
        SETTING_LAST_COUNTS: get_setting(SETTING_LAST_COUNTS, "") or "",
    }

    payload = fetch_github_export(repo=use_repo, branch=use_branch, token=use_token)
    result = import_exported_tables(payload["tables"], make_backup=make_backup)

    # Restore GitHub connection settings after full app_settings replace.
    for key, value in preserve.items():
        if value:
            set_setting(key, value)
        elif key == SETTING_TOKEN:
            set_setting(key, "")

    manifest = payload.get("manifest") or {}
    exported_at = manifest.get("exported_at") or ""
    pulled_at = _utc_now()

    set_setting(SETTING_LAST_PULL, pulled_at)
    if exported_at:
        set_setting(SETTING_LAST_EXPORT, exported_at)
    set_setting(SETTING_LAST_COUNTS, json.dumps(result["counts"]))

    return {
        "ok": True,
        "pulled_at": pulled_at,
        "exported_at": exported_at,
        "repo": payload["repo"],
        "branch": payload["branch"],
        "counts": result["counts"],
        "backup_path": result.get("backup_path"),
        "manifest": manifest,
    }


def import_from_local_data_dir(data_dir: str | Path, *, make_backup: bool = True) -> dict[str, Any]:
    """Import from a local data/ folder (same layout as the git export)."""
    root = Path(data_dir)
    if not root.exists():
        raise DatabaseError(f"Data folder not found: {root}")
    # Preserve phone-only GitHub connection settings across app_settings wipe.
    preserve = get_remote_config()
    preserve_meta = {
        SETTING_LAST_PULL: get_setting(SETTING_LAST_PULL, "") or "",
        SETTING_LAST_EXPORT: get_setting(SETTING_LAST_EXPORT, "") or "",
        SETTING_LAST_COUNTS: get_setting(SETTING_LAST_COUNTS, "") or "",
    }

    tables: dict[str, list] = {}
    for name in IMPORT_TABLES:
        path = root / f"{name}.json"
        if not path.exists():
            tables[name] = []
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise DatabaseError(f"{path.name} is not a JSON array.")
        tables[name] = payload

    manifest = {}
    manifest_path = root / "manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            manifest = {}

    result = import_exported_tables(tables, make_backup=make_backup)
    save_remote_config(
        repo=preserve["repo"],
        branch=preserve["branch"],
        token=preserve["token"],
    )
    for key, value in preserve_meta.items():
        if value:
            set_setting(key, value)

    pulled_at = _utc_now()
    set_setting(SETTING_LAST_PULL, pulled_at)
    if manifest.get("exported_at"):
        set_setting(SETTING_LAST_EXPORT, manifest["exported_at"])
    set_setting(SETTING_LAST_COUNTS, json.dumps(result["counts"]))
    return {
        "ok": True,
        "pulled_at": pulled_at,
        "exported_at": manifest.get("exported_at"),
        "counts": result["counts"],
        "backup_path": result.get("backup_path"),
        "source": str(root.resolve()),
    }
