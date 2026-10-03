---
name: up-banking-api
description: "Query Up bank: accounts, transactions, balances, spending."
version: 1.1.0
author: "up-banking-api-skill contributors (see CONTRIBUTING.md)"
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [finance, up-bank, banking, transactions, open-banking]
    related_skills: [stocks]
---

# Up Banking API Skill

Read-only access to Up (Australian neobank) account data through their public REST API.
Requires a Personal Access Token scoped to the user's own account.

## Links

| What | URL |
|------|-----|
| Up website | https://up.com.au |
| Features product tree | https://up.com.au/tree/ |
| Support | https://up.com.au/support/ |
| API documentation | https://developer.up.com.au |
| OpenAPI spec (GitHub) | https://github.com/up-banking/api |
| Community projects | https://github.com/up-banking/api/blob/master/community/EXAMPLES.md |
| API changelog | https://github.com/up-banking/api/issues/31 |

## When to Use

- User asks for their bank balance, recent transactions, or spending breakdown
- User wants to categorise a transaction or add/remove tags
- User mentions Up bank, their Up account, or asks about money in/out
- User wants to set up webhook notifications for new transactions
- Don't use for: other Australian banks' CDR/Open Banking data (separate API per bank)

## Prerequisites

1. An Up bank account (get it at https://up.com.au)
2. A Personal Access Token from the Up app: swipe right → Data sharing → Personal Access Token → Generate a token
3. Store the token with `hermes config set UP_BANKING_PAT <token>` — the full string including the `up:yeah:` prefix
4. Python 3.8+ and `curl`

## How to Run

The helper script wraps the common queries. Set the script path for easy reuse:

```bash
SCRIPT=~/.hermes/skills/finance/up-banking-api/scripts/up_client.py

python $SCRIPT ping
python $SCRIPT accounts
python $SCRIPT transactions
python $SCRIPT transactions --page-size 5
python $SCRIPT transactions --account-id <uuid>
python $SCRIPT account --account-id <uuid>
python $SCRIPT categories
python $SCRIPT webhooks
```

Or directly with curl (the `$UP_BANKING_PAT` env var is available inside Hermes sessions):

```bash
curl -s --globoff -H "Authorization: Bearer $UP_BANKING_PAT" \
  'https://api.up.com.au/api/v1/util/ping'

curl -s --globoff -H "Authorization: Bearer $UP_BANKING_PAT" \
  'https://api.up.com.au/api/v1/accounts'

curl -s --globoff -H "Authorization: Bearer $UP_BANKING_PAT" \
  'https://api.up.com.au/api/v1/transactions?page%5Bsize%5D=20'
```

## Commands

### `ping`
Connection health check. Returns a UUID and ⚡️ if the token is valid.

### `accounts`
List all accounts with ID, display name, balance, and type (TRANSACTIONAL or SAVER).

### `account --account-id <id>`
Get a single account by its UUID. Shows the same fields as `accounts` but for one account.

### `transactions [--account-id <id>] [--page-size N] [--json]`
Recent transactions, newest first. Default 20. Scope to one account with `--account-id`, adjust count with `--page-size`. Pass `--json` for structured output the agent can pipe through `jq` or Python for spending analysis — see the "For AI Agents" section in the README.

### `categories`
List all transaction categories with IDs.

### `webhooks`
List registered webhook endpoints with their active status.

### Write operations (curl only)
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

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /util/ping | Health check |
| GET | /accounts | List all accounts |
| GET | /accounts/{id} | Single account |
| GET | /accounts/{id}/transactions | Account-scoped transactions |
| GET | /transactions | All transactions |
| GET | /transactions/{id} | Single transaction |
| PATCH | /transactions/{id}/relationships/category | Set category |
| POST | /transactions/{id}/relationships/tags | Attach tags |
| DELETE | /transactions/{id}/relationships/tags | Detach tags |
| GET | /categories | List all categories |
| GET | /categories/{id} | Single category |
| GET | /tags | List all tags |
| POST | /webhooks | Create webhook |
| GET | /webhooks | List webhooks |
| DELETE | /webhooks/{id} | Delete webhook |
| POST | /webhooks/{webhookId}/ping | Test webhook |
| GET | /webhooks/{webhookId}/logs | Webhook delivery logs |

## Data Model

Responses follow JSON:API spec (`data` → array of resource objects, `links` for pagination).

**Account:** `id`, `displayName`, `accountType` (TRANSACTIONAL or SAVER), `ownershipType`, `balance` (currencyCode + value + valueInBaseUnits), `createdAt`.

**Transaction:** `id`, `status` (HELD or SETTLED), `rawText`, `description`, `amount` (currencyCode + value + valueInBaseUnits), `settledAt`, `createdAt`, category/tags relationships.

## Pitfalls

- **Square brackets in query params** need `--globoff` flag on curl, or URL-encode as `%5B`/`%5D` to avoid bash glob expansion.
- **Token includes the `up:yeah:` prefix** — store the full string as returned by the app. The API requires this prefix; stripping it causes a 401 error.
- **Rate limits** are undocumented but generous. Default page size is 20; max 50 per page for bulk pulls.
- **The PAT is personal** — it grants full read access to your accounts. Stored in `.env` via `hermes config set` — auto-redacted from Hermes logs by default.
- **Pagination** is cursor-based via `links.next`. The helper script shows a stderr message when more pages are available.
- **Webhooks** require a public callback URL. This skill lists and manages webhooks but does not include a receiver.
- **MSYS shell** on Windows: use `C:/...` paths for native tools; avoid `/tmp` for persistent files.

## Verification

```bash
SCRIPT=~/.hermes/skills/finance/up-banking-api/scripts/up_client.py
python $SCRIPT ping        # → pong — <uuid>
python $SCRIPT accounts    # → at least one account row
python $SCRIPT transactions  # → at least one transaction row
```

## Limitations

- **Read-only with exceptions:** categorisation and tagging are write endpoints; everything else is read-only. No funds transfer or payment initiation.
- **Beta API:** Endpoints may change. Features like scheduled payments and statements are not yet available via the API.
- **Personal scope only:** the PAT is scoped to the user's own accounts. No organisation/business access through this token type.
