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
- [Up Website](https://up.com.au)
- [Up Features & Product Tree](https://up.com.au/tree/)

## License

MIT — see [LICENSE](LICENSE).