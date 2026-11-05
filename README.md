# Empório da Música: customer service agent

A prototype of a text-based customer service agent for Empório da Música, a fictional musical instrument store in
Campo Grande/MS. It is my solution to the Artefact AI Engineer technical case.

The agent should take on the store's persona, answer from the material the store provided (operational data in CSV
files and a policy manual), know when to look up data (prices, stock, order status) and when to look up policies
(returns, opening hours, payment), and handle questions outside the store's scope.

> **Status:** in progress. This first version of the README describes the goal and how I am working. Instructions to run
> the project, the technical decisions and their justifications, the known limitations and the example conversations
> will be added as the project moves forward.

## How I work

I usually work with Claude Code as my main assistant. It is practical for the parts of a project that need context and
iteration: researching the problem, finding a basis for decisions and shaping the solution. For quick, specific
questions, formatting or a second opinion on a prompt, I switch to other common models such as GPT, Gemini or
DeepSeek. When a project needs something more specific or experimental, I use a harness like pi and pick a model from
a provider such as OpenRouter (for example [Xiaomi MiMo](https://openrouter.ai/xiaomi/mimo-v2.6-pro)).

The assistant speeds up research, writing and code, but the problem definition, the decisions, the checking of results
and the final organisation stay with me. I need to understand and be able to defend every part of what I deliver.

## How this project is being built

I split the work into four stages, and the commit history follows them:

1. **Understanding the problem.** I read the statement and the store material, and used Claude Code to help me
   understand the problem, research examples, models and good practices, and lay out the options for each decision
   (agent approach, model and provider, interface, conversation history, data handling). I used other models for quick
   questions and to check that my prompts were well written.
2. **Skeleton.** Based on those decisions, the basic structure of the solution: folders, dependencies, configuration
   and empty modules.
3. **Development.** I built step by step: data loading, tools, prompt and interface, tested along the way, with
   small commits. Using an agent to help with repetitive tasks when necessary, but always checking and fixing the outcome.
4. **Evaluation and delivery.** Review of the whole solution, example conversations and the final README.


## Store material

The store provided six CSV tables and a policy manual, kept in `data/` as received. Before designing the agent I
checked them with pandas:
- [docs/data.md](docs/data.md): what each file holds, what the agent uses it for, and what the checks found
  (reproducible with `python scripts/audit_data.py`).
- [docs/inconsistencies.md](docs/inconsistencies.md): contradictions and gaps in the material (two phone numbers,
  conflicting instalment rules, order totals that don't match their items, a shared customer e-mail...) and the simple
  handling chosen for each one.

## The problem in one picture

The diagram is written in [Mermaid](https://mermaid.js.org/), a way of writing diagrams as text. GitHub renders it
directly, it is versioned like code, and it is easy to change by hand or with an AI assistant.

```mermaid
flowchart LR
    C(["Customer"]) <-->|"message / answer"| A["Agent<br/>LLM + system prompt<br/>(persona and rules)"]

    subgraph open["Open to anyone"]
        SP["search_products<br/>get_product"]
        GP["get_policy"]
    end
    subgraph private["Only after identification"]
        ID["identify_customer<br/>(phone)"]
        OR["get_my_orders"]
    end

    A --> SP & GP & ID
    ID -->|"customer stored in the session"| OR
    A --> OR

    SP --> CAT[("products, categories,<br/>promotions")]
    GP --> MAN[("policy manual")]
    ID --> CUS[("customers")]
    OR --> ORD[("orders, order items")]
```

- The agent decides, at each message, whether it can answer directly, whether it needs **data** (catalogue, orders) or a
  **policy** (hours, payment, returns, shipping), or whether the question is outside the store's scope.
- Questions about the store, its products and its rules are open to anyone. Questions about a customer's own orders
  first require identification, which is checked in code.

## Technical decisions

The decisions and their justifications are recorded in [docs/decisions.md](docs/decisions.md): function calling with a
few typed tools, the policy manual as a tool, no agent framework, OpenRouter with a configurable model, customer
identification by phone, a CLI interface, in-memory history, pandas for the data and a Portuguese system prompt.

## Working with AI assistants

[AGENTS.md](AGENTS.md) holds the rules I give to coding assistants in this repository: where facts can come from, how
privacy is enforced, what must never be committed, and that every change is reviewed and committed by me.
