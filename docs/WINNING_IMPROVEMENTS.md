# Sentinel AI — Winning Improvements

Ranked by **impact on judging score** vs. **implementation time**. All
"Under 2 hours" items are realistic to add before submission if time
remains.

---

## Tier 1 — High impact, under 2 hours

| Improvement | Impact | Time | Notes |
|---|---|---|---|
| **Record a polished demo video using `docs/DEMO_SCRIPT.md`** | ⭐⭐⭐⭐⭐ | 30–45 min | Many hackathons weight the video heavily; a clean run-through of the live agent network + verdict report is your strongest asset. |
| **Add screenshots/GIF to README** | ⭐⭐⭐⭐ | 15 min | Run the app, capture the hero, live-agent animation, and final report. Drop into `docs/screenshots/`. |
| **"Agent reasoning trace" expandable panel in the UI** | ⭐⭐⭐⭐ | 45–60 min | Add a collapsible `<details>` per agent card showing full `reasoning` + `evidence` + `metadata` — reinforces "Explainable AI" criterion directly in the live demo. |
| **Confidence breakdown visualization** | ⭐⭐⭐ | 30 min | Small horizontal bar per agent showing `confidence` (0–1) next to risk score — visually demonstrates the Judge's "confidence-weighted aggregation" claim. |
| **Add a "Why this verdict?" tooltip/expand on the Judge card** | ⭐⭐⭐ | 20 min | Surface `report.reasoning` more prominently — it's already in the data, just needs UI emphasis. |
| **Populate Team section in README** | ⭐⭐⭐ | 5 min | Trivial but judges notice empty placeholders. |

---

## Tier 2 — High impact, 2–4 hours

| Improvement | Impact | Time | Notes |
|---|---|---|---|
| **Wire up real Foundry Agent Service** (if Azure access available) | ⭐⭐⭐⭐⭐ | 1–3 hrs | Follow `docs/FOUNDRY_UPGRADE.md`. Even partial — e.g. just the Knowledge Agent on real Foundry with `azure-ai-search` — visibly differentiates from "just an OpenAI wrapper." |
| **Admin/Analytics screen** | ⭐⭐⭐⭐ | 2–3 hrs | New `/analytics` page: aggregate stats across past investigations (verdict distribution, scam category breakdown, agent agreement rate). Store results in-memory or SQLite for the demo. |
| **Multi-language scam detection** (Hindi/Tamil/regional) | ⭐⭐⭐⭐ | 2–4 hrs | Extend `data/scam_kb.json` with regional-language keywords; update Content Agent prompt to detect code-mixed text. High relevance for India-focused judging. |
| **Investigation history / shareable report link** | ⭐⭐⭐ | 1–2 hrs | Persist `InvestigationReport` by ID (SQLite or in-memory dict), add `GET /api/investigations/{id}` + a `/report/[id]` Next.js page. |
| **Real Azure AI Search-backed Knowledge Agent** | ⭐⭐⭐⭐ | 2–3 hrs | Replace `data/scam_kb.json` lookup with a vector index — the single most "Foundry-native" upgrade beyond the agent service itself. |

---

## Tier 3 — Foundry-specific enhancements

| Improvement | Impact | Time | Notes |
|---|---|---|---|
| Provision all 5 agents in Foundry portal, screenshot the Agents tab | ⭐⭐⭐⭐ | 30 min (after upgrade) | Visual proof of "real Foundry Agent Service" for judges who check. |
| Show a live thread/run trace from the Foundry portal during demo | ⭐⭐⭐⭐ | 0 min extra | Just have the portal open in a second tab during the live demo. |
| Add a second function tool: `lookup_sender_domain_reputation` for Identity Agent | ⭐⭐⭐ | 1 hr | Even a mocked WHOIS-style lookup demonstrates tool-calling breadth. |
| Foundry "Connected Agents" hand-off pattern (Judge invokes specialists directly) | ⭐⭐⭐ | 3+ hrs | Bigger architectural change — good "future work" talking point if not implemented. |

---

## Tier 4 — UI polish

| Improvement | Impact | Time | Notes |
|---|---|---|---|
| Loading skeleton / shimmer on agent cards before first event | ⭐⭐ | 20 min | Smooths the "running" state visually. |
| Color-coded evidence tags by source agent | ⭐⭐⭐ | 30 min | E.g. small colored dot per evidence line indicating which agent produced it — reinforces multi-agent narrative. |
| Animated risk gauge counts up from 0 to final score | ⭐⭐ | 20 min | Small `requestAnimationFrame` tween on `RiskGauge`. |
| Dark/light theme toggle | ⭐ | 30 min | Low judging impact, nice-to-have. |
| Mobile responsiveness pass | ⭐⭐ | 30 min | Verify hero + diagram + report on narrow viewports. |

---

## Tier 5 — Demo-day improvements

| Improvement | Impact | Time | Notes |
|---|---|---|---|
| Pre-warm the mock/Foundry client before the demo (run one dummy investigation) | ⭐⭐⭐ | 1 min | Avoids any first-call latency or cold-start surprises on stage. |
| Have 3 pre-tested samples ready (scam, borderline, safe) | ⭐⭐⭐⭐ | 10 min | Already built into the UI (`SAMPLES` array in `page.tsx`) — just rehearse the click order. |
| Keep `/docs` (Swagger UI) open in a tab as backup if frontend has issues | ⭐⭐⭐ | 0 min | `POST /api/investigate` works standalone — solid fallback. |
| Print/display the Foundry provider chain diagram during the "Foundry section" of the talk | ⭐⭐⭐ | 10 min | Makes the fallback architecture concrete and memorable. |

---

## Recommended execution order (if time-boxed)

1. Populate README Team section (5 min)
2. Pre-test all 3 demo samples + pre-warm client (15 min)
3. Add confidence bars + "Why this verdict?" emphasis to UI (45 min)
4. Take screenshots, add to README (15 min)
5. Record demo video using the script (45 min)
6. **If Azure access available:** wire up real Foundry Agent Service for at
   least the Knowledge Agent (remaining time)
