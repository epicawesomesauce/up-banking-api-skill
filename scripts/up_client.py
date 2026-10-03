#!/usr/bin/env python3
"""Up Banking API client — wraps the most common queries."""

import json
import hashlib
import os
import sys
import tempfile
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


def _req_paginated(path: str, limit: int = 1000, use_cache: bool = True) -> list:
    """Fetch ALL results following links.next, up to `limit`."""
    import time

    cache = None
    if use_cache:
        cache_dir = os.path.join(tempfile.gettempdir(), "up-api-cache")
        os.makedirs(cache_dir, exist_ok=True)
        cache_key = hashlib.sha256((path + f":{limit}").encode()).hexdigest()[:16]
        cache = os.path.join(cache_dir, cache_key)
        age = time.time() - os.path.getmtime(cache) if os.path.exists(cache) else None
        if age is not None and age < 900:  # 15 min TTL
            with open(cache) as f:
                return json.load(f)

    tok = _token()
    all_data = []
    next_url = BASE + path
    while next_url and len(all_data) < limit:
        req = urllib.request.Request(next_url, headers={"Authorization": f"Bearer {tok}"})
        try:
            with urllib.request.urlopen(req) as resp:
                resp_data = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            print(f"error: HTTP {e.code} — {body}", file=sys.stderr)
            sys.exit(1)
        all_data.extend(resp_data.get("data", []))
        next_url = resp_data.get("links", {}).get("next") or ""

    all_data = all_data[:limit]

    if use_cache and cache:
        with open(cache, "w") as f:
            json.dump(all_data, f)
    return all_data


def _cmd_accounts(json_output=False, use_cache=True):
    data = _req_paginated("/accounts", limit=100, use_cache=use_cache)
    if json_output:
        print(json.dumps(data, indent=2))
        return
    for acct in data:
        a = acct["attributes"]
        bal = a["balance"]["value"]
        print(f"{acct['id']:36s}  {a['displayName']:20s}  ${bal:>8}  {a['accountType']}")


def _cmd_accounts_json(account_id=None, since=None, until=None, category=None,
                      status=None, page_size=100, limit=1000, use_cache=True, json_output=False):
    """Fetch transactions with filters, following pagination."""
    path = f"/accounts/{account_id}/transactions" if account_id else "/transactions"
    params = []
    if since:
        params.append(f"filter%5Bsince%5D={since}T00:00:00%2B10:00")
    if until:
        params.append(f"filter%5Buntil%5D={until}T23:59:59%2B10:00")
    if category:
        params.append(f"filter%5Bcategory%5D={category}")
    if status:
        params.append(f"filter%5Bstatus%5D={status}")
    params.append(f"page%5Bsize%5D={page_size}")
    param_str = "&".join(params)
    path = path + "?" + param_str

    data = _req_paginated(path, limit=limit, use_cache=use_cache)
    if json_output:
        print(json.dumps(data, indent=2))
        return
    for t in data:
        a = t["attributes"]
        amt = a["amount"]["value"]
        desc = a["description"]
        st = a["status"]
        dt = a.get("settledAt") or a.get("createdAt", "")
        print(f"{dt[:10] if dt else 'pending':10s}  ${amt:>8}  {st:7s}  {desc}")


def cmd_ping():
    data = _req("/util/ping")
    mid = data.get("meta", {}).get("id", "?")
    print(f"pong — {mid}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: up_client.py <ping|accounts|account|transactions|categories|webhooks> [--account-id <id>] [--page-size <n>] [--since YYYY-MM-DD] [--until YYYY-MM-DD] [--category <slug>] [--status SETTLED|HELD] [--limit N] [--no-cache] [--json]", file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[1]
    account_id = None
    page_size = 100
    limit = 1000
    since = None
    until = None
    category = None
    status = None
    use_cache = True
    json_output = "--json" in sys.argv

    def _get_arg(flag):
        if flag in sys.argv:
            idx = sys.argv.index(flag)
            if idx + 1 < len(sys.argv):
                return sys.argv[idx + 1]
        return None

    def _get_int_arg(flag, default):
        val = _get_arg(flag)
        if val:
            try:
                return max(1, int(val))
            except ValueError:
                print(f"error: {flag} must be a number", file=sys.stderr)
                sys.exit(1)
        return default

    account_id = _get_arg("--account-id")
    since = _get_arg("--since")
    until = _get_arg("--until")
    category = _get_arg("--category")
    status = _get_arg("--status")
    page_size = _get_int_arg("--page-size", 100)
    limit = _get_int_arg("--limit", 1000)
    if "--no-cache" in sys.argv:
        use_cache = False

    if cmd == "ping":
        cmd_ping()
    elif cmd == "accounts":
        _cmd_accounts(json_output, use_cache)
    elif cmd == "account":
        if not account_id:
            print("error: --account-id is required for the account command", file=sys.stderr)
            sys.exit(1)
        data = _req(f"/accounts/{account_id}")
        acct = data.get("data", {})
        if not acct:
            print(f"error: account '{account_id}' not found", file=sys.stderr)
            sys.exit(1)
        if json_output:
            print(json.dumps(acct, indent=2))
            sys.exit(0)
        a = acct["attributes"]
        bal = a["balance"]["value"]
        print(f"ID:       {acct['id']}")
        print(f"Name:     {a['displayName']}")
        print(f"Balance:  ${bal}")
        print(f"Type:     {a['accountType']}")
        print(f"Created:  {a['createdAt'][:10]}")
    elif cmd == "transactions":
        _cmd_accounts_json(account_id, since, until, category, status,
                         page_size, limit, use_cache, json_output)
    elif cmd == "categories":
        data = _req_paginated("/categories", limit=200, use_cache=use_cache)
        if json_output:
            print(json.dumps(data, indent=2))
        else:
            for cat in data:
                print(f"{cat['id']:36s}  {cat['attributes'].get('name','')}")
    elif cmd == "webhooks":
        data = _req_paginated("/webhooks", limit=100, use_cache=use_cache)
        for wh in data:
            a = wh["attributes"]
            print(f"{wh['id']:36s}  {a.get('url','')}  active={a.get('isActive', False)}")
    else:
        print(f"error: unknown command '{cmd}'", file=sys.stderr)
        sys.exit(1)
