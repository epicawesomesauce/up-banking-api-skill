# Contributing

Thanks for taking an interest. This repo is a Hermes Agent skill for the Up Banking API — small scope, small surface.

## How to contribute

1. Open an issue describing the change (bug, missing endpoint, docs fix).
2. Fork the repo, make your change on a descriptive branch.
3. Open a pull request linking the issue.

Keep changes scoped to the skill and its helper script. If you're adding a new API endpoint, make sure it exists in the live API first (check https://developer.up.com.au).

## Standards

- **SKILL.md** — follows the [Hermes Agent skill authoring standard](https://github.com/NousResearch/hermes-agent). Description ≤ 60 chars, frontmatter complete, no personal data.
- **scripts/up_client.py** — Python stdlib only (no pip deps). argparse-style flags, stderr for errors, stdout for data.
- **README.md** — keep the For AI Agents section accurate. It's what agents read when deciding how to invoke the skill.
- **No personal data** — account IDs, balances, or tokens must never appear in committed files.

## Upstream PR

When the skill is mature enough, the goal is to contribute it to `NousResearch/hermes-agent/optional-skills/finance/up-banking-api/`. At that point the CONTRIBUTING process shifts to the main Hermes repo. This repo remains the development staging ground.

## Questions

Open an issue. If it's about the Up API itself (endpoint behaviour, missing features), direct it to https://github.com/up-banking/api instead.