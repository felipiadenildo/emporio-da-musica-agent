# Technical decisions

A short record of the decisions taken before writing the code, with the reasoning and the alternatives considered. The
statement says there is no right answer and asks for the reasoning; this file is where it lives. The README summarises
it. Decisions are numbered so later changes can refer to them.

Guiding principle: **the simplest design that answers correctly**. The case is a prototype, the store material is small,
and what matters is that prices, stock, orders and rules are never invented.

---

### D1. Agent approach: function calling with a few typed tools

**Decision.** The LLM answers the customer and, when it needs a fact, calls one of a few Python functions (tools). Data
questions go to catalogue and order tools; rule questions go to a policy tool.

**Why.** Every price, stock level or order status in an answer comes from a tool result, never from the model's memory.
The tool calls also make the required behaviour visible: in the example conversations you can see *when* the agent
decided to query data and when it looked up a policy. Typed tools only allow the queries I designed, which is safer
than letting the model write its own.

**Alternatives.**
- *RAG with embeddings:* the standard choice for large document collections. The manual has 8 pages (about 1,750
  words), so retrieval would add failure modes (a table split across chunks, a missed passage) and solve nothing.
- *SQL agent (text-to-SQL):* flexible, but the model could write wrong queries or read the customers table freely.
- *ReAct by prompting:* the same reason-act-observe idea, but native tool calling is more reliable today.

### D2. Policies: one tool that returns a section of the manual

**Decision.** The manual is split into its numbered sections (store data, hours, payment, returns, shipping, promotions,
service guidelines, warranty, privacy). The system prompt lists the section titles, and the tool `get_policy(section)`
returns the text of one section.

**Why.** The statement explicitly evaluates "knowing when to consult policies". With a tool, that decision is an
observable action that shows up in the transcripts. The prompt stays short, and the same design works if the manual
grows. Splitting by the numbered headings is cheap and needs no search engine.

**Alternative.** Put the whole manual in the system prompt. It fits (a few thousand tokens) and is even simpler, and it
would also be a valid choice. I chose the tool because it makes the behaviour the case asks for explicit.

### D3. No agent framework

**Decision.** A small loop written with the provider's SDK: send the conversation and the tool definitions, run the tools
the model asks for, send the results back, repeat until the model answers in text.

**Why.** Four or five tools don't need a framework. The loop is short, and I can explain every line of it.

**Alternatives.** LangChain/LangGraph, PydanticAI, OpenAI Agents SDK. I would consider one of them if the agent grew:
several agents, long-running state, built-in tracing.

### D4. Model and provider: OpenRouter, Claude Haiku 5.5 by default, configurable

**Decision.** The code uses the `openai` Python SDK, which speaks the OpenAI-compatible API. The endpoint, the key and
the model come from environment variables. The default is OpenRouter with `anthropic/claude-haiku-5.5`.

**Why.** A customer service agent needs reliable tool calling, good Brazilian Portuguese, low latency and low cost. In
the OpenRouter model list (checked on 2026-11-04), Claude Haiku 5.5 supports tools and costs US$ 0.10 per million input
tokens and US$ 0.50 per million output tokens. OpenRouter gives access to many models with one key, which is also how I
work day to day. Because the endpoint is configurable, the same code runs against OpenAI directly or a local model
served by Ollama, without changes.

**Alternatives.** A direct provider SDK (best fidelity, but tied to one vendor); a local model (free and private, but
small local models are weaker at tool calling and Portuguese).

### D5. Customer identification before personal data

**Decision.** General store information (products, prices, hours, policies) is open to anyone. Anything that depends on
a customer's data (their orders) requires identification first. The agent asks for the customer's **phone number**, the
tool `identify_customer` checks it against the customer table, and the identified customer is stored **in the session,
in code**. The order tool only returns orders of that customer, whatever the model asks for.

**Why.** This is what real service agents do before talking about an order, and it follows the manual's privacy section
(LGPD). The check lives in the code, not in the prompt, so a customer can't talk the model into showing someone else's
order. The phone is used because it is unique in the data (two customers share an e-mail, see
[inconsistencies.md](inconsistencies.md#7-two-customers-share-an-e-mail)) and it is the natural identifier on a WhatsApp
channel.

**Limitation, stated openly.** A phone number alone is weak authentication: anyone who knows it could see the orders. A
real system would use a unique document such as the CPF combined with a second factor (a one-time code sent to the
phone, or the order number). The data has no CPF and the prototype has no messaging, so the phone is the simplification.

### D6. Interface: command line

**Decision.** A CLI chat. `--debug` prints each tool call and its result; `--save` writes the conversation to a Markdown
file.

**Why.** The statement says the focus is the agent working correctly. A CLI needs no extra dependencies, and the saved
transcripts become the example conversations, so they are real runs and not hand-written.

### D7. Conversation history: in memory, per session

**Decision.** The message list is kept in memory during the session and can be exported with `--save`. No database.

**Why.** Multi-turn context is needed ("and the other model?"), but remembering customers across sessions adds storage
and privacy concerns without improving the prototype.

### D8. Data handling: pandas in memory

**Decision.** The CSVs are loaded once with pandas at start-up, with the light treatment described in
[data.md](data.md). The PDF manual is read with `pypdf`, so `data/` stays exactly as received.

**Why.** A few hundred rows don't need a database. Inconsistencies are handled as described in
[inconsistencies.md](inconsistencies.md).

### D9. Prompt strategy

**Decision.** A system prompt in Portuguese, the customer's language, built from the manual's service guidelines
(section 7):
- **persona:** the store's virtual assistant, "informal but professional", like a friend who understands music;
- **style:** short, natural sentences as in a WhatsApp chat; a short list only when there are several options; prices
  always with the original value and the percentage when there is a promotion;
- **hard rules:** never state a price, stock level or delivery time without a tool result; no accessories (polite
  redirect); out-of-scope questions get a polite redirect; personal data only after identification; complaints and
  uncertain cases are handed over to the team;
- **context injected at start-up:** today's date and the store hours (to know whether the store is open).

No few-shot examples at first; add them only if a scenario fails.

### D10. API key

**Decision.** The key is read from the environment (a local `.env` file, ignored by git). The repository has a
`.env.example` and the README explains how to use your own key with OpenRouter, OpenAI or a local model.

**Why.** A key committed to a public repository is found and abused within minutes. Each evaluator can run the agent
with their own key in one step.

### D11. Tests: only what proves the critical rules

**Decision.** A few `pytest` tests on the tools, with no LLM: price with an active promotion, order refused without
identification, identification by phone. The rest is checked through the example conversations, comparing every number
with the CSV files.

**Why.** These are the rules where a mistake would harm a customer or the store. The tests are fast and need no API key.
