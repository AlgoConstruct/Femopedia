# Femopedia v1 — Anonymous AI Health Q&A

**Date:** 2026-09-23
**Status:** Approved design, ready for implementation planning
**Scope:** First shippable slice of the Femopedia platform described in `docs/Vision&Strategy.md`

---

## 1. Context and scope

`docs/Vision&Strategy.md` describes a ten-year platform: longitudinal health continuity, fourteen personas, a multi-agent architecture, community, telehealth, marketplace, and a global expansion sequence. That document is the destination. This spec is the first step toward it.

The build is solo, assisted by AI, with no engineering team and no clinical staff. The first market is Nepal and South Asia. Those two facts set the size of v1: one loop, built well, rather than a thin version of the full MVP list.

### The v1 loop

A woman asks a question about her body, cycle, sex, or mood, in her own language, without telling anyone who she is, and gets an answer that is accurate, kind, sourced, and knows when to stop and point her to a human.

### In scope

- Anonymous chat. A device token is issued on first open. No signup. Conversations are stored server-side against that token and never against a personal identifier.
- Language matching across Devanagari Nepali, Romanized Nepali, Hinglish, and English.
- Retrieval-grounded answers with visible sources and stated uncertainty.
- A hard safety layer: crisis breakout, and refusal on dosing, diagnosis, and unsupervised abortion-medication instructions.
- Per-answer feedback and an opt-in evaluation corpus.
- Account upgrade by phone or email, offered only once history is worth keeping.
- Real deletion: one button, wiping device and server state.

### Out of scope for v1

All of the following appear in the strategy document and are deliberately deferred:

- Cycle, symptom, mood, and sleep logging, and the health timeline built on them
- Community
- Doctor summary export and appointment preparation
- Telehealth, marketplace, Partner Mode, Family Mode
- Native mobile applications
- Payments and subscription

### Success criteria

One hundred real Nepali-speaking women use the product; at least 60% of first sessions are rated useful; zero unsafe answers survive review; at least 30% of users return within four weeks. Downloads and signups are not success criteria.

---

## 2. Architecture

### Request path

```
PWA (TanStack Start, existing frontend/)
   |  HTTPS, device token in header
   v
Django + DRF
   |
   +-- 1. Jev triage      (safety + routing, one call)
   +-- 2. Retrieval        Chroma + Neo4j
   +-- 3. Generation       OpenAI, streamed
   +-- 4. Jev post-gate    (verify drafted answer)
   +-- 5. Persist          Postgres, LangSmith trace
   |
Celery + Redis: embedding jobs, evaluation jobs
```

### Stack

| Concern | Choice | Notes |
| --- | --- | --- |
| Backend | Django 5 + DRF | Monorepo: existing `frontend/`, new `backend/` |
| Relational store | Postgres 16 | Source of truth |
| Vector store | ChromaDB | Qdrant later; accessed only through `knowledge/retriever.py` |
| Graph store | Neo4j Community | Domain relations and deterministic red-flag rules |
| Generation | OpenAI, pinned model version | Called through the LangChain chat model interface so the provider stays swappable |
| Decisions and safety | Jev (TypeSafe AI) via `langchain-typesafe` | Typed probabilistic decisions, 70–500ms, $0.042/MTok input, free output |
| Orchestration | LangGraph | Pipeline as explicit nodes with conditional edges |
| Tracing and evaluation | LangSmith | Stores confidence scores for threshold tuning |
| Queue | Celery + Redis | |
| Deployment | Docker Compose on a single VPS | No Kubernetes, no microservices |

LangChain is used for the model interface, retrievers, and document loaders only. Control flow belongs to LangGraph.

### Django applications

Each has one purpose:

- `accounts` — device tokens, account upgrade, deletion
- `chat` — conversations, messages, the streaming endpoint
- `safety` — Jev gates, crisis policy, refusal rules, audit log
- `knowledge` — content entries, embeddings, retrieval, graph queries
- `evals` — feedback, evaluation corpus, review queue

### Why Jev sits in front of generation

The crisis path must never depend on a generative model behaving well. Jev returns typed values constrained to a schema defined in advance, with a calibrated confidence per answer, in under half a second, at a cost low enough to run on every message including every model output.

An important correction to the vendor framing: "cannot hallucinate" means Jev cannot emit a value outside the declared schema or of the wrong type. It does not mean the decision is correct. Crisis detection remains a probabilistic call, so this design sets explicit confidence thresholds biased toward false positives on crisis. That is a policy decision made here, not a property the model provides.

---

## 3. Data model

### Postgres — source of truth

```
Device          id, token_hash, created_at, locale, last_seen
Account         id, device_id FK, phone_e164?, email?, verified_at
                (nullable; most users never create one)
Conversation    id, device_id FK, started_at, title_auto
Message         id, conversation_id FK, role, body, lang_detected,
                created_at, jev_pre_json, jev_post_json, model_id, latency_ms
MessageSource   id, message_id FK, content_entry_id, chunk_id, score
Feedback        id, message_id FK, verdict, reason?, note?
SafetyEvent     id, message_id FK, class, confidence, action_taken,
                reviewed_by?, reviewed_at?
ContentEntry    id, slug, title, body_md, lang, tier, reviewer,
                reviewed_at, sources_json, status
ConsentFlag     device_id FK, eval_corpus_optin, created_at
```

`jev_pre_json` and `jev_post_json` store every noul's value together with its confidence. That is the dataset used to tune thresholds.

`Message.body` is encrypted at rest at the application layer. Deletion is a hard cascade from `Device`, not a soft flag.

### Chroma — retrieval

One collection per language: `ne`, `ne-rom`, `hi`, `en`. Chunk metadata carries `content_entry_id`, `tier`, `lang`, `topic_ids`, `lifestage_ids`.

Chroma holds derived data only and is rebuildable from Postgres by a Celery job. This is what makes the later move to Qdrant a reindex rather than a migration.

### Neo4j — domain graph

```
(:Symptom)-[:SUGGESTS {strength}]->(:Condition)
(:Condition)-[:COMMON_IN]->(:LifeStage)
(:Condition)-[:RED_FLAG_FOR]->(:UrgencyLevel)
(:Topic)-[:PREREQUISITE_OF]->(:Topic)
(:ContentEntry)-[:EXPLAINS]->(:Topic|:Condition|:Symptom)
(:Myth)-[:CONTRADICTED_BY]->(:ContentEntry)
```

Two query-time jobs:

1. **Retrieval expansion.** Vector search alone tends to return near-duplicate chunks. Given "irregular periods and hair growth", the graph walks `SUGGESTS` to PCOS and pulls the entries that explain it.
2. **Red-flag lookup.** Deterministic. If the extracted symptom set touches a `RED_FLAG_FOR` edge, escalation is raised regardless of what the model would have said.

The `Myth` node type is specific to this market. Where taboo suppresses accurate information, inherited misinformation fills the gap. A mapped myth graph lets an answer name and correct the belief the user actually holds rather than answering a textbook question she did not ask.

The v1 graph is small and hand-authored: roughly 60 symptoms, 25 conditions, 8 life stages, 40 myths. It is a curated knowledge asset, not a scraped one.

---

## 4. Safety layer

Three classes of intervention, each with distinct behavior.

### Class A — Crisis breakout

Triggers: self-harm or suicidal intent; disclosed physical or sexual violence; obstetric emergency (heavy bleeding in pregnancy, severe abdominal pain, reduced fetal movement); suspected overdose or poisoning.

Behavior: normal flow stops and no generation call is made. A fixed, human-written response is shown, authored in Nepali and English rather than generated. It acknowledges what she said, states plainly that this needs a person now, and gives the relevant helpline and nearest-care guidance. The conversation stays open, and every subsequent turn re-runs the gate.

Threshold: deliberately low, starting at confidence 0.35. A false positive shows a woman a helpline she did not need. A false negative is the failure this layer exists to prevent. The threshold may be lowered freely; it is never raised without reviewing the misses that motivated the change.

### Class B — Hard refusal with redirect

Triggers: requests for medication dosing; requests for a diagnosis; requests for unsupervised abortion-medication instructions; requests to interpret lab results or imaging.

Behavior: the question as asked is not answered. One sentence explains why, without moralizing. The surrounding education that is safe to give is still given: what the condition is, what a clinician will ask, what a visit costs and involves, and where to go. Threshold 0.6, since these are usually unambiguous in phrasing.

On abortion specifically, and this matters in this market: refusing to give dosing is not refusing the topic. The product must still explain what Nepali law permits, that legal services exist, and where they are. Silence pushes women toward the unsafe informal market, which is the harm the refusal exists to prevent. A refusal that causes that harm has failed.

### Class C — Post-generation veto

The Jev post-gate reads the drafted answer before the user sees the end of it. If `contains_dosage`, `contains_diagnosis`, or `unsupported_claim` fires above threshold, the answer is discarded and a fallback is shown. Every veto writes a `SafetyEvent` and enters the review queue.

Streaming: buffer the stream, gate it, then release. Text that may have to be retracted is never shown.

### Always on

Every answer carries a visible source. Uncertainty is stated in words rather than hidden. No answer claims to diagnose. A positive `minor_signal` shifts tone and content toward age-appropriate education.

### Helpline numbers — launch blocker

Nepal's national mental health helpline is believed to be 1166 and the National Women Commission helpline 1145. These are not confident enough to ship on. Before v1 reaches a single real user, every number must be confirmed directly with the operating organization, along with the hours it is actually answered and whether it is answered in Nepali. A helpline that rings out is worse than no helpline, because she will not try twice.

### Review queue

Every `SafetyEvent` and every thumbs-down is reviewed weekly at minimum, with Jev confidence scores visible. That review is what moves thresholds. No part of the safety layer is set-and-forget.

---

## 5. Product surface

### Screens

1. **Open** — no splash, no signup, no onboarding carousel. A text box, one line describing what this is, and three example questions in Nepali that a real woman would be embarrassed to ask aloud. Time to first question under ten seconds.
2. **Chat** — the product. Streaming answer, sources collapsed beneath it, thumbs up and down on every assistant message, and chips for "explain simpler" and "in Nepali".
3. **History** — past conversations, keyed to the device token and served from the server, with IndexedDB as a local cache for fast and offline load. Long-press to delete one. An account upgrade binds the device token to an account so history survives a change of device.
4. **Settings** — language preference, evaluation-corpus opt-in defaulting to off, delete everything, what is stored, who we are.
5. **Save your history** — the account upgrade, shown after roughly five conversations or at delete-risk moments, never on first open.

### Deliberate absences

No streaks, no notifications in v1, no profile. Engagement mechanics attached to a product about shame and pain convert badly and read as manipulation. Section 3.4 of the strategy document already commits against them.

### Answer shape

Enforced in the system prompt and checked by the post-gate:

```
Direct answer in two to three sentences, in her language, no preamble
What is actually happening, plainly, without jargon
When this needs a doctor
Source chips, and: this is education, not diagnosis
```

The "when this needs a doctor" line appears on every health answer, including reassuring ones. It is what separates this from a chatbot and the first thing a clinician will check under scrutiny.

### Content

Target for v1: 40 tier-1 reviewed entries covering what Nepali women search for and cannot ask aloud — menstrual irregularity, PCOS, white discharge, contraception options and access, UTI, first sex and pain, pregnancy signs, abortion law and legal access, postpartum bleeding, mood and cycle, and marital pressure around fertility. Each entry exists in Nepali and English, carries sources, is reviewed, and is mapped into the graph with its associated myths.

At least one Nepali clinician (MBBS or nurse-midwife) must sign off on tier-1 content. This is not substitutable by AI. Budget a small honorarium; it is the one line item a solo build cannot skip.

### Voice

Warm, direct, never coy. Uses the actual Nepali words for body parts rather than euphemism, because euphemism is what she is already drowning in. Answers the question first, then says when a doctor is genuinely needed — never using "consult your doctor" as a way to avoid answering.

---

## 6. Routing and cost control

Jev runs on every message for safety. Output tokens are free and input costs $0.042 per million tokens, so asking it twenty further questions within that same call costs effectively nothing. Every routing decision therefore lives in that one call.

### The `jev_triage` node

```
safety    crisis_self_harm, abuse_disclosure, obstetric_emergency,
          seeks_dosing, seeks_diagnosis, abortion_med_instructions,
          minor_signal

routing   intent          greeting | chitchat | informational_health
                          | personal_health_concern | emotional_support
                          | product_meta | out_of_domain | service_abuse
          is_faq          -> faq_id (cardinality 255, maps to ContentEntry)
          needs_retrieval  bool
          complexity       low | medium | high
          history_turns    0-20
          emotional_load   low | medium | high
          language         ne | ne-rom | hi | en
```

### Conditional edges

| Jev verdict | Path | Generation tokens |
| --- | --- | --- |
| crisis | fixed human-written response | none |
| greeting, chitchat | templated reply, warm | none |
| product_meta | static content | none |
| out_of_domain, service_abuse | templated redirect | none |
| `is_faq` at high confidence | the reviewed ContentEntry served in her language | none |
| informational, complexity low | cheap model, top-3 chunks, 0–2 history turns | small |
| personal_health_concern, or complexity high | frontier model, top-8 chunks, full history, graph expansion | full |

### Where the savings come from, largest first

1. **Zero-generation paths.** Greetings, chitchat, out-of-domain messages, and FAQ hits never reach the generation model. In consumer health chat these are not a rounding error; a large share of opening messages are greetings, "are you real", and the same recurring dozen questions.
2. **`history_turns`.** Naive chat resends the whole conversation each turn, growing quadratically. Deciding that a message is a fresh question needing zero prior turns, rather than a follow-up needing four, is the largest recurring saver on long conversations.
3. **Model routing by complexity.** Simple factual questions do not need the expensive model.
4. **Retrieval gating.** `needs_retrieval = false` skips chunk injection entirely.

### Two rules that override cost

- **The safety gate runs on every message regardless of intent.** A crisis message can arrive looking like chitchat. Safety is never on a cost-optimized path.
- **Uncertainty routes upward, never downward.** Where `intent` or `complexity` confidence falls below threshold, the expensive path is taken. The cheap path must be opted into by confidence; the full path is the default. A wrong cheap answer to a frightened woman costs more than the tokens it saved.

### Agent-side gating

When tools are introduced after v1 (symptom extraction, care-locator lookup), `AutoModeMiddleware` checks each tool call before execution rather than trusting the generating model's judgment.

### Expected effect

An estimated 40–60% reduction in generation tokens against routing everything through the frontier model, most of it from the first two items. This is a hypothesis to be measured in the alpha through LangSmith, not a guarantee. Jev's own cost is negligible against either figure.

---

## 7. Build sequence

Each phase ends with something usable rather than a half-layer.

**P0 — Foundation (week 1).** Monorepo restructure, Django project, Docker Compose for Postgres, Redis, Chroma, and Neo4j, device-token auth, health check. Done when a request carrying a device token round-trips.

**P1 — Content and graph (weeks 1–4, parallel to everything).** Author 40 entries in Nepali and English, map the graph, obtain clinician sign-off. Starts first because it is the long pole and cannot be parallelized by adding compute.

**P2 — Safety gate standalone (week 2).** Jev pre-gate and post-gate as a LangGraph node pair, with the golden set below. Built and tested before the pipeline it guards exists. Done when the evaluation suite passes.

**P3 — Retrieval (week 3).** Chroma ingest job, language-filtered search, Neo4j expansion, red-flag lookup. Done when a query returns the correct entries with sources.

**P4 — Answer pipeline (week 4).** LangGraph assembly, OpenAI generation, streaming with buffered gate release, persistence, LangSmith tracing.

**P5 — PWA (weeks 5–6).** Five screens on the existing TanStack application, streaming UI, history read from the server with an IndexedDB cache, deletion, settings.

**P6 — Closed alpha (week 7 onward).** Twenty to thirty women recruited by hand. Weekly review of every flagged conversation and every thumbs-down. Thresholds tuned on their real messages rather than synthetic ones.

---

## 8. Testing

- **Safety golden set.** Roughly 200 hand-labeled messages across Nepali, Romanized Nepali, and English: direct crisis phrasings, euphemistic crisis phrasings in Nepali idiom, dosing requests, benign questions that read as alarming, and alarming questions that read as benign. Runs on every commit. Crisis recall is the release gate; nothing ships with a miss.
- **Refusal set.** Confirms Class B refuses the dosing while still delivering the surrounding education. A refusal that teaches nothing is a failed test.
- **Retrieval set.** Fifty questions with expected source entries, measured on recall@5.
- **Django suite.** pytest, factory_boy, real Postgres in CI.
- **LangSmith datasets** mirror the golden sets so threshold changes are compared against history rather than judged by feel.

---

## 9. Risks

1. **Content is the bottleneck, not code.** Forty reviewed bilingual entries is the hardest item here and the most likely to slip. It starts in week 1 and ships in batches; the product can launch with 25.
2. **Clinician sign-off.** Solo builders routinely skip this and then cannot defend a single answer. Secure one named reviewer before P4.
3. **Nepali answer quality.** Unknown until measured. Retrieval grounding reduces the model's freedom, the alpha measures quality directly, and the fallback is tighter templating with more pre-written content.
4. **Operational load of four datastores, solo.** Docker Compose on one VPS, daily Postgres backups. Chroma and Neo4j are both rebuildable from Postgres, so only one store is precious.
5. **Distribution.** How a woman in Nepal finds this is unsolved, out of v1 scope, and the most likely cause of the project failing. Flagged here rather than solved.

---

## 10. Sources

- TypeSafe AI, "Introducing System One Models and Jev" — https://typesafe.ai/blog/introducing-system-one-models-and-jev
- LangChain, "Building a harness with Jev" — https://www.langchain.com/blog/building-a-harness-with-jev
