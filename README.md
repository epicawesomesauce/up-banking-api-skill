# Up Banking API — Hermes Agent Skill

> **AI-generated disclaimer:** This skill was developed with the assistance of an AI agent (Hermes Agent). It has been tested against the live Up API and verified working. Review the code before use, especially the credential-handling in `scripts/up_client.py`.

Read-only access to [Up Bank](https://up.com.au) (Australian neobank) account data through their public REST API. Check balances, list transactions, categorise spending, manage tags, and set up webhooks — all from within a Hermes Agent session.

## Scope

- **Accounts** — list all accounts with balances, types, and IDs
- **Transactions** — recent transactions across all accounts or per account, with adjustable page size
- **Categories & Tags** — list, categorise transactions, attach/remove tags
- **Webhooks** — create, list, and manage webhook notifications
- **Ping** — connection health check

This is a **personal-scope** integration. The API token grants access only to the user's own accounts. No funds transfer, no payment initiation, no third-party access.

## Prerequisites

- [Up Bank](https://up.com.au) account
- Personal Access Token (Up app → swipe right → Data sharing → Personal Access Token → Generate)
- [Hermes Agent](https://hermes-agent.nousresearch.com) installed
- Python 3.8+ and `curl`

## Install

```bash
# Register the repo as a skill tap
hermes skills tap add epicawesomesauce/up-banking-api-skill

# Install the skill
hermes skills install epicawesomesauce/up-banking-api-skill/up-banking-api

# Store your API token
hermes config set UP_BANKING_PAT <your-token>

# Verify it works
cd ~/.hermes/skills
find . -name up_client.py -path "*/up-banking-api/*"
# then cd to that directory and run python scripts/up_client.py ping
```

Or install directly from URL:
```bash
hermes skills install https://raw.githubusercontent.com/epicawesomesauce/up-banking-api-skill/main/SKILL.md --name up-banking-api
```

## Usage

```bash
# From inside the installed skill directory:
python scripts/up_client.py ping
python scripts/up_client.py accounts
python scripts/up_client.py transactions
python scripts/up_client.py transactions --page-size 5
python scripts/up_client.py transactions --account-id <uuid> --page-size 50
python scripts/up_client.py categories
python scripts/up_client.py webhooks
```

## For AI Agents

This section is for AI agents (including Hermes) that load this skill and need to know how to operate it correctly.

### When to load this skill
- The user asks about their bank balance, spending, or recent transactions
- The user wants to categorise a transaction or manage tags
- The user mentions their Up bank account

### Credential resolution order
The helper script reads the token in this priority:
1. `$UP_BANKING_PAT` environment variable (set inside Hermes sessions by `.env`)
2. `~/.hermes/.env` or `$LOCALAPPDATA/hermes/.env` (parsed directly for standalone runs)
3. `~/.hermes/secrets/up-banking-pat` (legacy fallback)

The token includes the `up:yeah:` prefix — do not strip it. Store the full string.

### Script invocation
Set a path variable for clean reuse:
```
SCRIPT=~/.hermes/skills/finance/up-banking-api/scripts/up_client.py
```
Then call `python $SCRIPT <command> [flags]`.

All output is plain-text tabular format on stdout. Errors go to stderr and exit non-zero. The `transactions` command prints a `(more available — follow: <url>)` message on stderr when pagination has more results — you do not need to follow it unless the user asks for older transactions.

### Available commands

| Command | Flags | Returns |
|---------|-------|---------|
| `ping` | — | row: `pong — <uuid>` |
| `accounts` | — | table: id, name, balance, type |
| `account` | `--account-id <id>` | labelled fields: ID, Name, Balance, Type, Created |
| `transactions` | `--account-id <id>`, `--page-size <n>`, `--json` | table or full JSON with all attributes |
| `categories` | — | table: id, name |
| `webhooks` | — | table: id, url, active |

### Categorising and tagging (curl only)
The helper script does not wrap write operations. Use curl directly:

```bash
curl -s --globoff -X PATCH -H "Authorization: Bearer $UP_BANKING_PAT" \
  -H "Content-Type: application/json" \
  -d '{"data":{"type":"categories","id":"<category-id>"}}' \
  'https://api.up.com.au/api/v1/transactions/<tx-id>/relationships/category'
```

To find a category ID, run `python $SCRIPT categories` and grep the name.

### Pitfalls for agents
- The `up:yeah:` prefix is required — never strip it. The API returns 401 without it.
- Square brackets `[]` in query params need URL-encoding (`%5B`/`%5D`) or `--globoff` on curl — raw brackets break bash's glob expansion.
- The PAT grants full read access to all accounts. Never log it, echo it, or include it in tool output meant for the user.
- If the helper script exits with "set UP_BANKING_PAT via \`hermes config set\`", either the env var is missing or the `.env` file wasn't found. Check both `.env` locations.
- Paginated responses include a `links.next` URL in the JSON body — the helper script surfaces this on stderr but does not auto-follow. Only fetch next pages if the user asks for more history.

## API Coverage

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /util/ping | Health check |
| GET | /accounts | List all accounts |
| GET | /accounts/{id} | Get account |
| GET | /accounts/{id}/transactions | Account transactions |
| GET | /transactions | All transactions |
| GET | /transactions/{id} | Single transaction |
| PATCH | /transactions/{id}/relationships/category | Categorise |
| POST | /transactions/{id}/relationships/tags | Add tags |
| DELETE | /transactions/{id}/relationships/tags | Remove tags |
| GET | /categories | List categories |
| GET | /tags | List tags |
| POST | /webhooks | Create webhook |
| GET | /webhooks | List webhooks |
| DELETE | /webhooks/{id} | Delete webhook |

## Links

- [Up API Documentation](https://developer.up.com.au)
- [Up API OpenAPI Spec (GitHub)](https://github.com/up-banking/api)
- [Community API projects](https://github.com/up-banking/api/blob/master/community/EXAMPLES.md)
- [Up Website](https://up.com.au)
- [Up Features & Product Tree](https://up.com.au/tree/)

## License

MIT — see [LICENSE](LICENSE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).