#!/usr/bin/env python3
"""Up Banking API client — wraps the most common queries."""

import json
import os
import sys
import urllib.request
import urllib.error

BASE = "https://api.up.com.au/api/v1"


def _env_paths():
    """Return possible .env paths in priority order."""
    paths = []
    # 1. HERMES_HOME env var
    hh = os.environ.get("HERMES_HOME")
    if hh:
        paths.append(os.path.join(hh, ".env"))
    # 2. AppData/local (canonical for Windows desktop app)
    localappdata = os.environ.get("LOCALAPPDATA")
    if localappdata:
        paths.append(os.path.join(localappdata, "hermes", ".env"))
    # 3. User home (canonical for CLI)
    paths.append(os.path.expanduser("~/.hermes/.env"))
    return paths


def _dotenv_val(key):
    """Read a key from the first .env file that contains it."""
    for env_path in _env_paths():
        try:
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(key + "="):
                        val = line.split("=", 1)[1].strip()
                        val = val.strip("\"'")
                        if val:
                            return val
        except (FileNotFoundError, PermissionError, OSError):
            continue
    return None


def _token():
    # 1. environment variable (set when running inside Hermes)
    tok = os.environ.get("UP_BANKING_PAT")
    if tok:
        return tok
    # 2. .env files (AppData first, then home)
    tok = _dotenv_val("UP_BANKING_PAT")
    if tok:
        return tok
    # 3. legacy file-based storage
    path = os.path.expanduser("~/.hermes/secrets/up-banking-pat")
    try:
        with open(path) as f:
            return f.read().strip()
    except FileNotFoundError:
        pass
    print("error: set UP_BANKING_PAT via `hermes config set UP_BANKING_PAT <token>`", file=sys.stderr)
    sys.exit(1)


def _req(path: str) -> dict:
    tok = _token()
    url = BASE + path
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}"})
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"error: HTTP {e.code} — {body}", file=sys.stderr)
        sys.exit(1)


def cmd_ping():
    data = _req("/util/ping")
    mid = data.get("meta", {}).get("id", "?")
    print(f"pong — {mid}")


def cmd_accounts():
    data = _req("/accounts")
    for acct in data.get("data", []):
        a = acct["attributes"]
        bal = a["balance"]["value"]
        print(f"{acct['id']:36s}  {a['displayName']:20s}  ${bal:>8}  {a['accountType']}")


def cmd_transactions(account_id=None):
    path = f"/accounts/{account_id}/transactions" if account_id else "/transactions"
    path += "?page%5Bsize%5D=20"
    data = _req(path)
    for t in data.get("data", []):
        a = t["attributes"]
        amt = a["amount"]["value"]
        desc = a["description"]
        st = a["status"]
        dt = a.get("settledAt") or a.get("createdAt", "")
        print(f"{dt[:10] if dt else 'pending':10s}  ${amt:>8}  {st:7s}  {desc}")
    links = data.get("links", {})
    if links.get("next"):
        print(f"\n(more available — follow: {links['next']})", file=sys.stderr)


def cmd_categories():
    data = _req("/categories")
    for cat in data.get("data", []):
        rel = data.get("included", [])
        print(f"{cat['id']:36s}  {cat['attributes'].get('name','')}")


def cmd_webhooks():
    data = _req("/webhooks")
    for wh in data.get("data", []):
        a = wh["attributes"]
        print(f"{wh['id']:36s}  {a.get('url','')}  active={a.get('isActive', False)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: up_client.py <ping|accounts|transactions|categories|webhooks> [--account-id <id>]", file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[1]
    account_id = None
    if "--account-id" in sys.argv:
        idx = sys.argv.index("--account-id")
        if idx + 1 < len(sys.argv):
            account_id = sys.argv[idx + 1]

    if cmd == "ping":
        cmd_ping()
    elif cmd == "accounts":
        cmd_accounts()
    elif cmd == "transactions":
        cmd_transactions(account_id)
    elif cmd == "categories":
        cmd_categories()
    elif cmd == "webhooks":
        cmd_webhooks()
    else:
        print(f"error: unknown command '{cmd}'", file=sys.stderr)
        sys.exit(1)
