# Sentinel AI — Submission Package

---

## Tagline (10 alternatives)

1. Four agents investigate. One judge decides.
2. Multi-agent reasoning for a single-agent world of scams.
3. Don't just detect scams — investigate them.
4. Every verdict, explained. Every agent, accountable.
5. Scam detection that shows its reasoning.
6. A second opinion for every suspicious message — times four.
7. Built on Microsoft Foundry. Built to explain itself.
8. The investigation team your inbox never had.
9. Reasoning agents. Real evidence. Real verdicts.
10. Scam intelligence, by committee.

---

## Elevator Pitch (30 seconds)

Sentinel AI is a multi-agent scam investigation network built on Microsoft
Foundry. Instead of one model guessing, four specialist agents — Content,
Pattern, Knowledge, and Identity — independently investigate a suspicious
message in parallel. A Judge Agent then weighs their findings, resolves
disagreements, and delivers a single explainable verdict: a risk score,
evidence trail, and concrete recommendations. It's scam detection that
shows its work — and it runs reliably from free-tier accounts all the way
up to full Foundry Agent Service in production.

---

## Judge Pitch (90 seconds)

Scam messages — fake bank alerts, lottery wins, job offers demanding
"registration fees," OTP phishing — are everywhere, and they keep evolving.
Most detection tools run a single model and return a single number, with no
explanation. That's a trust problem: users can't tell if a flag is real, and
they can't appeal a black box.

Sentinel AI investigates the way a security team would. Our Orchestrator
Agent dispatches a message **in parallel** to four specialists: a Content
Agent reading tone and manipulation tactics, a Pattern Agent matching known
scam templates, a Knowledge Agent grounding the analysis against a threat
intelligence database — sourced from RBI, CERT-In, and SEBI advisories — and
an Identity Agent checking for sender spoofing and brand impersonation.

All four results stream live to the user via Server-Sent Events, so you
literally watch the investigation happen. Then our Judge Agent — the
reasoning centerpiece — performs confidence-weighted aggregation, resolves
disagreements between agents, categorizes the scam type, and writes a
multi-step reasoning narrative explaining its verdict.

On the Foundry side, each of these five agents is architected as a
persistent Foundry Agent using Threads, Runs, and function tools — the
Knowledge Agent's grounded retrieval and the Judge's audit-trail tool are
both real Foundry tool calls. And because we built a layered fallback —
Foundry Agent Service, then Azure OpenAI, then OpenAI, then a deterministic
mock — this demo runs flawlessly even on a free-tier account, with zero code
changes required to go to full production Foundry.

Sentinel AI isn't a black box. It's an investigation, and you can see every
step of it.

---

## Short Description (50 words)

Sentinel AI is a multi-agent scam investigation network built on Microsoft
Foundry. Four specialist agents — Content, Pattern, Knowledge, and Identity —
analyze suspicious messages in parallel, streaming live results. A Judge
Agent aggregates their evidence into one explainable verdict: risk score,
evidence, and recommendations.

*(50 words)*

---

## Medium Description (150 words)

Sentinel AI is a multi-agent scam investigation network built for the
Microsoft Foundry Reasoning Agents track. Rather than relying on a single
model's guess, Sentinel AI dispatches every suspicious email, SMS, WhatsApp
message, or offer to four independent specialist agents running in
parallel: a Content Agent analyzing manipulation tactics, a Pattern Agent
matching known scam templates, a Knowledge Agent grounding its analysis
against a threat intelligence database of documented campaigns, and an
Identity Agent checking for sender spoofing and brand impersonation.

A Judge Agent then performs multi-step reasoning over all four findings —
weighing confidence, resolving disagreements, and categorizing the scam type
— before producing a final Scam Risk Report with a 0–100 risk score, a
verdict, a deduplicated evidence trail, and concrete recommendations. The
entire investigation streams live to the frontend, so users watch each agent
report its findings in real time. Built with a layered Foundry → Azure
OpenAI → OpenAI → mock fallback chain, Sentinel AI runs reliably anywhere.

*(150 words)*

---

## Long Description (500 words)

Scam messages are one of the most common and damaging forms of digital harm
people face every day — fake bank "KYC verification" alerts, lottery and
prize scams, work-from-home job offers that demand upfront fees, OTP
phishing, and government-impersonation threats. These messages are
constantly evolving to evade simple keyword filters, and the people most
likely to fall for them are often the least equipped to second-guess a
slick, official-looking message.

Most existing scam-detection tools take a single piece of text, run it
through one model, and return a single risk score. This is fast, but it's a
black box: the user has no way to understand *why* a message was flagged,
which both erodes trust in legitimate warnings and makes it impossible to
appeal a false positive. It also means the detector is only as good as one
model's single perspective on the text.

Sentinel AI takes a fundamentally different approach: **investigation
instead of classification**. When a user submits a suspicious message, our
Orchestrator Agent dispatches it simultaneously to four independent
specialist agents, each examining the message from a different angle:

- The **Content Agent** analyzes the linguistic and psychological dimension
  — urgency language, emotional manipulation, reward and threat baiting,
  and impersonation cues in the writing itself.
- The **Pattern Agent** matches the message's structure against a library of
  known scam templates — lottery and prize scams, advance-fee fraud,
  investment and crypto scams, job scams, OTP/SIM-swap fraud, and more —
  plus structural signals like shortened URLs and suspicious monetary
  patterns.
- The **Knowledge Agent** is our Foundry-grounded retrieval agent: it
  queries a curated threat intelligence knowledge base — built from RBI,
  CERT-In, SEBI, and TRAI advisories — to check whether the message matches
  a *documented* scam campaign, a known suspicious domain, or a tracked
  brand-impersonation target.
- The **Identity Agent** focuses on sender authenticity — domain spoofing
  patterns, brand impersonation, and the use of unofficial channels (a
  "bank" messaging from a personal Gmail or WhatsApp number, for example).

All four agents return structured results — a risk score, evidence list,
reasoning, and confidence — which stream live to the frontend via
Server-Sent Events. Users watch each agent "complete" in real time on an
animated agent-network diagram, making the multi-agent process visible
rather than hidden.

The results then flow to our **Judge Agent**, the system's reasoning
centerpiece. Rather than simply averaging four scores, the Judge performs
confidence-weighted aggregation, applies an agreement bonus when multiple
agents independently flag high risk, categorizes the scam type, and writes
a multi-step reasoning narrative explaining exactly how it reached its
verdict. The final **Scam Risk Report** includes a 0–100 risk score, a
verdict (SCAM / LIKELY SCAM / SUSPICIOUS / LIKELY SAFE / SAFE), a
deduplicated evidence trail attributed back to source agents, and concrete,
actionable recommendations.

On the Microsoft Foundry side, each of Sentinel AI's five agents is designed
as a persistent Foundry Agent using Threads, Runs, and function-calling
tools — the Knowledge Agent's retrieval and the Judge's audit-trail logging
are both real Foundry tool calls, giving every investigation a fully
inspectable reasoning trace. A layered fallback chain (Foundry Agent Service
→ Azure OpenAI → OpenAI → deterministic mock) ensures the system runs
reliably from a free-tier account all the way to full production Foundry,
with zero changes to agent code.

*(500 words)*
