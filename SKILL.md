---
name: up-banking-api
description: "Query Up bank: accounts, transactions, balances, spending."
version: 1.0.0
author: up-banking-api-skill contributors (spheraz), Hermes Agent
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
3. Store the token with `hermes config set UP_BANKING_PAT <token>` (saves to `~/.hermes/.env`)
4. `curl` available in PATH (pre-installed on all platforms)

## How to Run

```bash
curl -s --globoff -H "Authorization: Bearer $UP_BANKING_PAT" 'https://api.up.com.au/api/v1/util/ping'
```

If the ping returns a `meta.id`, the connection works.

## Usage

The helper script at `scripts/up_client.py` wraps the common queries (run from the skill's installed directory or using its full path):

```bash
python scripts/up_client.py ping
python scripts/up_client.py accounts
python scripts/up_client.py transactions
python scripts/up_client.py transactions --account-id <id>
python scripts/up_client.py transactions --page-size 5
python scripts/up_client.py categories
```

Or directly with curl:

```bash
# Ping
curl -s --globoff -H "Authorization: Bearer $UP_BANKING_PAT" 'https://api.up.com.au/api/v1/util/ping'

# List accounts
curl -s --globoff -H "Authorization: Bearer $UP_BANKING_PAT" 'https://api.up.com.au/api/v1/accounts'

# Recent 20 transactions
curl -s --globoff -H "Authorization: Bearer $UP_BANKING_PAT" 'https://api.up.com.au/api/v1/transactions?page%5Bsize%5D=20'

# Account-specific transactions
curl -s --globoff -H "Authorization: Bearer $UP_BANKING_PAT" 'https://api.up.com.au/api/v1/accounts/ACCOUNT_ID/transactions?page%5Bsize%5D=20'
```

## Quick Reference

| Action | Command |
|--------|---------|
| Ping | `python scripts/up_client.py ping` |
| Accounts | `python scripts/up_client.py accounts` |
| Transactions | `python scripts/up_client.py transactions` |
| Account txs | `python scripts/up_client.py transactions --account-id <id>` |
| Last N txs | `python scripts/up_client.py transactions --page-size 5` |
| Categories | `python scripts/up_client.py categories` |
| Categorise tx | `PATCH /transactions/{id}/relationships/category` |
| Add tags | `POST /transactions/{id}/relationships/tags` |
| Remove tags | `DELETE /transactions/{id}/relationships/tags` |
| Webhooks | `python scripts/up_client.py webhooks` |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /util/ping | Health check — returns a UUID |
| GET | /accounts | List all accounts |
| GET | /accounts/{id} | Single account with balance |
| GET | /accounts/{id}/transactions | Account-scoped transactions |
| GET | /transactions | All transactions (paginated) |
| GET | /transactions/{id} | Single transaction detail |
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

## Procedure

### 1. First-time setup
Generate a PAT in the Up app (swipe right → Data sharing → Personal Access Token). Store it with `hermes config set UP_BANKING_PAT <token>`.

### 2. Verify connectivity
```bash
curl -s --globoff -H "Authorization: Bearer $UP_BANKING_PAT" 'https://api.up.com.au/api/v1/util/ping'
```
Expected: `{"meta":{"id":"<uuid>","statusEmoji":"⚡️"}}`

### 3. Pull account data
List all accounts with `python scripts/up_client.py accounts` to get account IDs, names, types, and balances.

### 4. Pull transactions
Use `python scripts/up_client.py transactions` for the most recent 20 across all accounts, or scope to one account with `--account-id`. Adjust the count with `--page-size 5`.

### 5. Categorise or tag (optional)
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
```

## Data Model

Accounts have: `id`, `displayName`, `accountType` (TRANSACTIONAL or SAVER), `ownershipType`, `balance` (currencyCode + value + valueInBaseUnits), `createdAt`.

Transactions have: `id`, `status` (HELD or SETTLED), `rawText`, `description`, `amount`, `settledAt`, `createdAt`, `category` relationship, `tags` relationship.

All responses follow JSON:API spec (`data` → array of resource objects, `links` for pagination).

## Pitfalls

- **Square brackets in query params** need `--globoff` flag on curl, or URL-encode as `%5B`/`%5D` — otherwise bash's glob expansion eats them.
- **Token is read from file every time** — there's no caching; each curl command reads it fresh. Keep the file as a single line with no trailing spaces.
- **Rate limits** are generous but undocumented. Space requests across the page size (50/page) for bulk history pulls.
- **The PAT is personal** — it has full read access to the user's accounts. Never log it, echo it, or save it in conversation transcripts. Stored in `.env` via `hermes config set` — auto-redacted from logs by default.
- **If `.env` isn't loaded** (e.g. running the script outside Hermes), fallback reads `~/.hermes/secrets/up-banking-pat` if it exists.
- **"up:yeah:" prefix** is part of the visual token format in the UI but the API accepts only the raw hex string — strip any prefix before saving.
- **Pagination** uses cursor-based `links.next`. Following it requires appending the `next` URL's query string to the base URL. The helper script does this automatically.
- **MSYS shell note** on Windows: native tools need `C:/...` paths; `/tmp` works for scratch but avoid it for persistent files.
- **Webhooks** deliver events to a callback URL. The payload format is documented but the skill does not include a webhook receiver — you need a public endpoint to receive them.

## Verification

```bash
python scripts/up_client.py ping  # returns pong with UUID
python scripts/up_client.py accounts  # at least one account
python scripts/up_client.py transactions  # non-empty list
```

All three pass → the skill is fully operational. The token is valid, endpoints work, and the helper script is wired correctly.

## Limitations

- **Read-only with exceptions:** categorisation and tagging are write endpoints; everything else is read-only. No funds transfer or payment initiation.
- **Beta API:** Up's API is still in beta. Endpoints may change, and some features (scheduled payments, statements) are not yet available.
- **Personal scope only:** the PAT is scoped to the user's own accounts. No organisation/business account access through this token type.
