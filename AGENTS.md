# Instructions for coding assistants

Rules for any AI coding assistant working in this repository (I use Claude Code; the file also works for other tools that
read `AGENTS.md`). They keep the assistant's output consistent with the decisions in [docs/decisions.md](docs/decisions.md).

## Context
- Prototype of a customer service agent for a fictional music store. Read `README.md` and `docs/decisions.md` first.
- Keep it simple: no agent framework, no database, no extra dependencies without a reason written in `docs/decisions.md`.

## Rules
- **Language:** code, comments, docs and commit messages in English. Everything the agent says to the customer is in
  Brazilian Portuguese.
- **Facts come from tools:** the agent must never state a price, stock level, order detail or policy that didn't come
  from a tool result. Don't add hard-coded facts about the store to prompts or code.
- **Privacy:** order data is only returned for the customer identified in the session. Enforce it in code, not only in
  the prompt.
- **Data:** `data/` holds the store material as received. Never edit it; treat inconsistencies as documented in
  `docs/inconsistencies.md`.
- **Secrets:** never write API keys in code, docs or tests. Keys live only in `.env`, which is ignored by git.
- **Tests:** run `pytest` before proposing a commit. Tests must not call the LLM.
- **Changes:** small and focused, one step at a time. Explain what changed and why; I review, run and commit every change
  myself.
