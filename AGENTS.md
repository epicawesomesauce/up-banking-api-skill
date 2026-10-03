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

Pass `--json` to `accounts`, `account`, `transactions`, or `categories` to get the full JSON:API resource objects instead of formatted tables. Pipe through `jq` or Python for spending analysis:

```bash
python $SCRIPT transactions --page-size 50 --json | \
  jq 'map(select(.attributes.status == "SETTLED"))
     | group_by(.attributes.description)
     | map({category: .[0].attributes.description,
            total: (map(.attributes.amount.value | tonumber) | add)})
     | sort_by(-.total) | .[:5]'
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