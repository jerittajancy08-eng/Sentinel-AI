# Sentinel AI — 3-Minute Hackathon Demo Script

**Track:** Microsoft Agents League Hackathon — Reasoning Agents
**Total time:** ~3:00
**Presenters:** 1–2 people (one talking, one driving the demo, or one person doing both)

---

## [0:00–0:25] Opening

> "Hi judges — we're Team Sentinel, and we built **Sentinel AI**: a
> multi-agent scam investigation network on Microsoft Foundry.
>
> Our pitch in one line: **four independent AI agents investigate a
> suspicious message in parallel, and a Judge Agent reasons over their
> findings to deliver one explainable verdict** — not a black-box score,
> but a real investigation."

---

## [0:25–0:55] The Problem

> "Scam messages — fake bank alerts, lottery wins, job offers, OTP
> phishing — are everywhere, and they're getting more sophisticated every
> month. Most detection tools run a single model and spit out a number with
> no explanation. Users don't know *why* something was flagged, so they
> either ignore real warnings or panic over false positives.
>
> We wanted something that investigates the way a security team would:
> multiple specialists, each looking at a different angle, and a senior
> reviewer who weighs all their findings."

---

## [0:55–1:25] Architecture — Show the Agent Network

*(Switch to the Sentinel AI landing page — the agent network diagram is
visible)*

> "Here's our architecture. The **Orchestrator** receives the message and
> dispatches it **in parallel** to four specialist agents:
>
> - The **Content Agent** reads tone — urgency, emotional manipulation,
>   reward and threat baiting.
> - The **Pattern Agent** matches the message structure against known scam
>   templates — lottery scams, advance-fee fraud, job scams, OTP fraud.
> - The **Knowledge Agent** queries our Sentinel threat intelligence base —
>   this is our Foundry-grounded knowledge retrieval, matching against
>   documented campaigns, suspicious domains, and brand-impersonation
>   targets.
> - The **Identity Agent** checks sender authenticity — domain spoofing,
>   brand impersonation, unofficial channels.
>
> All four run **simultaneously**, then everything flows into the **Judge
> Agent**, which is the real reasoning centerpiece — it weighs each agent's
> confidence, resolves disagreements, and writes a final verdict."

---

## [1:25–2:25] Live Demo — Run an Investigation

*(Paste the sample "Lottery / KYC Phishing" message, click **Run
Investigation**)*

> "Let's investigate a real-looking message: 'Your SBI account will be
> suspended, verify your KYC immediately, click this link... congratulations,
> you've also won ₹50,000.'
>
> Watch the network — all four agents activate at once."

*(Let the diagram animate — agents light up and report scores live via
SSE)*

> "Content Agent: high risk — urgency and reward-baiting language.
> Pattern Agent: matches our 'Lottery / Prize Scam' and 'Phishing Attack'
> templates, and flags the shortened URL.
> Knowledge Agent: this is the Foundry-grounded piece — it's matched this
> against our 'Bank KYC Phishing' campaign in the threat database, sourced
> from RBI threat intelligence, AND flagged the domain as a known
> blocklisted shortener.
> Identity Agent: detects SBI brand impersonation — the message claims to
> be from SBI but provides no official verification path."

*(Judge Agent activates, then the report renders)*

> "And here's the Judge's verdict: **SCAM, risk score 94, HIGH
> confidence**, categorized as 'Bank KYC Phishing.' Below that — the full
> evidence trail from all four agents, deduplicated and prioritized, plus
> concrete recommendations: don't click, block the sender, report to
> cybercrime.gov.in, never share OTPs.
>
> Every single claim in this report traces back to a specific agent's
> finding — that's our explainability story."

*(Optional, if time allows — paste the "Legitimate Message" sample)*

> "And for contrast — a normal meeting reminder. Score: 5. Verdict: SAFE.
> The system isn't just trigger-happy; it differentiates."

---

## [2:25–2:50] Microsoft Foundry Section

> "Under the hood, every agent call routes through our Foundry abstraction
> layer. In its fullest form, each of these five agents — Content, Pattern,
> Knowledge, Identity, and Judge — is a **persistent Foundry Agent**, run
> via **Threads and Runs**, with the Knowledge Agent using a **function tool**
> to query our threat intelligence base — that's Foundry's grounded
> retrieval in action. The Judge Agent uses a second tool to log every
> specialist's finding, giving us a full audit trail of the reasoning
> process — directly in the Foundry portal.
>
> And critically — if Foundry Agent Service, or Azure OpenAI, isn't
> available, the system automatically falls back through Azure OpenAI, then
> OpenAI, then a deterministic mock mode. That's why this demo just works,
> right now, on a free-tier account — and scales straight to full Foundry
> in production with zero code changes in the agents themselves."

---

## [2:50–3:00] Closing — Why Sentinel AI Is Different

> "Most scam detectors give you a number. Sentinel AI gives you an
> **investigation** — four independent perspectives, a Judge that reasons
> about disagreement, grounded threat intelligence, and a verdict you can
> actually trust and explain to someone else.
>
> That's Sentinel AI — multi-agent reasoning, built on Microsoft Foundry,
> ready to protect real people from real scams. Thank you."

---

## Backup talking points (Q&A)

- **"What if two agents disagree?"** — The Judge Agent is explicitly
  instructed to weigh grounded findings (Knowledge Agent KB matches,
  Identity Agent spoofing detection) more heavily than purely linguistic
  signals, and explains *why* in its reasoning narrative.
- **"How does this scale?"** — Stateless FastAPI service, agents run as
  async tasks; horizontal scaling is just more App Service instances. The
  Knowledge Agent's JSON KB is designed as a drop-in replacement target for
  Azure AI Search.
- **"What about other languages / regional scams?"** — The threat KB and
  agent prompts are easily extended; see `docs/WINNING_IMPROVEMENTS.md` for
  our multi-language roadmap.
