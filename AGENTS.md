# Up Banking API — Agent Instructions

This file is consumed by AI agents (Hermes, Claude Code, etc.) that need to operate this skill correctly. Humans should read [README.md](README.md) instead.

## When to load this skill

- The user asks about their bank balance, spending, or recent transactions
- The user wants to categorise a transaction or manage tags
- The user mentions their Up bank account

## Credential resolution order

The helper script reads the token in this priority:

1. `$UP_BANKING_PAT` environment variable (set inside Hermes sessions via `.env`)
2. `~/.hermes/.env` or `$LOCALAPPDATA/hermes/.env` (parsed directly for standalone runs)
3. `~/.hermes/secrets/up-banking-pat` (legacy fallback)

The token includes the `up:yeah:` prefix — do not strip it. Store the full string.

## Script invocation

Set a path variable for clean reuse:

```
SCRIPT=~/.hermes/skills/finance/up-banking-api/scripts/up_client.py
```

Then call `python $SCRIPT <command> [flags]`.

All output is plain-text tabular format on stdout. Errors go to stderr and exit non-zero. The `transactions` command prints a `(more available — follow: <url>)` message on stderr when pagination has more results — do not follow it unless the user asks for older transactions.

## Available commands

| Command | Flags | Returns |
|---------|-------|---------|
| `ping` | — | row: `pong — <uuid>` |
| `accounts` | — | table: id, name, balance, type |
| `account` | `--account-id <id>` | labelled fields: ID, Name, Balance, Type, Created |
| `transactions` | `--account-id <id>`, `--page-size <n>`, `--json` | table or full JSON with all attributes |
| `categories` | — | table: id, name |
| `webhooks` | — | table: id, url, active |

Pass `--json` to `accounts`, `account`, `transactions`, or `categories` to get the full JSON:API resource objects instead of formatted tables. Pipe through `jq` or use the analysis script for spending breakdowns:

```bash
# Spending summary by category
python scripts/analysis.py summary --days 30

# HTML spending widget (generates a ::preview for Hermes desktop)
python scripts/analysis.py widget --days 14
```

The widget command outputs a `::preview{file=...}` directive. In the Hermes desktop app this renders as a live styled card inline in the chat. In other environments the file path is printed on stderr.

## Hermes-exclusive features

### Spending widget (::preview)
Run `python scripts/analysis.py widget --days N` to generate a horizontal bar chart of your top spending categories. The HTML uses the app's theme variables (`--foreground`, `--muted-foreground`, `--border`) so it matches the current skin. Best at 14-30 day range.

### Cron — recurring reports
Use `cronjob_manage` to schedule daily balance snapshots or weekly spending digests:

```python
from hermes_tools import cronjob_manage

cronjob_manage(
    action="create",
    name="up-daily-balance",
    schedule="0 9 * * *",       # 9am daily
    goal="Run python ~/.hermes/skills/finance/up-banking-api/scripts/up_client.py accounts and summarize the balances. Use ::preview to render an HTML table if the desktop app is available.",
)

cronjob_manage(
    action="create",
    name="up-weekly-spending",
    schedule="0 10 * * 1",      # 10am Monday
    goal="Run python ~/.hermes/skills/finance/up-banking-api/scripts/analysis.py summary --days 7 and present the weekly spending breakdown.",
)
```

The cron goal text tells the agent what to do — it reads the skill, runs the script, and delivers the result to the user's home channel on the configured messaging platform.

### Large transaction alerts
Use `cronjob_manage` with a higher frequency and a custom curl command:

```python
cronjob_manage(
    action="create",
    name="up-large-tx-check",
    schedule="*/30 * * * *",    # every 30 min
    goal="Check the last 5 transactions from the Up Banking API. If any have an absolute amount over $100 and status HELD, alert the user with the transaction details.",
)
```

## Write operations (curl only)

The helper script does not wrap write operations. Use curl directly:

```bash
# Categorise a transaction
curl -s --globoff -X PATCH -H "Authorization: Bearer $UP_BANKING_PAT" \
  -H "Content-Type: application/json" \
  -d '{"data":{"type":"categories","id":"<category-id>"}}' \
  'https://api.up.com.au/api/v1/transactions/<tx-id>/relationships/category'

# Add tags
curl -s --globoff -X POST -H "Authorization: Bearer $UP_BANKING_PAT" \
  -H "Content-Type: application/json" \
  -d '{"data":[{"type":"tags","id":"<tag-name>"}]}' \
  'https://api.up.com.au/api/v1/transactions/<tx-id>/relationships/tags'

# Remove tags
curl -s --globoff -X DELETE -H "Authorization: Bearer $UP_BANKING_PAT" \
  'https://api.up.com.au/api/v1/transactions/<tx-id>/relationships/tags'
```

To find a category ID, run `python $SCRIPT categories` and grep the name.

## Pitfalls

- **The `up:yeah:` prefix is required** — never strip it. The API returns 401 without it.
- **Square brackets `[]` in query params** need URL-encoding (`%5B`/`%5D`) or `--globoff` on curl — raw brackets break bash's glob expansion.
- **The PAT grants full read access** to all accounts. Never log it, echo it, or include it in tool output meant for the user.
- **If the helper script exits with "set UP_BANKING_PAT via \`hermes config set\`"**, either the env var is missing or the `.env` file wasn't found. Check both `~/.hermes/.env` and `$LOCALAPPDATA/hermes/.env`.
- **Paginated responses** include a `links.next` URL in the JSON body. The helper script surfaces this on stderr but does not auto-follow. Only fetch next pages if the user asks for more history.