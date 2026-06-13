# Microsoft Foundry Agent Service — Migration Plan

## Goal

Upgrade Sentinel AI from "Azure OpenAI chat completions wrapped in a
Foundry-flavored client" to **real Microsoft Foundry Agent Service**:
persistent agents, threads, runs, and tool-calling — while keeping every
existing code path working as a fallback.

## What changed (already implemented)

| File | Change |
|---|---|
| `core/foundry_agent_service.py` | **New.** Wraps `azure-ai-projects` / `azure-ai-agents` SDKs. Provisions 5 named Foundry Agents (Content, Pattern, Knowledge, Identity, Judge), each with its own `instructions` and tools. Runs each specialist in an isolated thread per investigation. |
| `core/foundry_client.py` | `FoundryLLMClient` now checks `foundry_agent_service.is_available()` first. If a Foundry project endpoint is configured and the SDK is installed, **every** `complete()` call routes through real Foundry Agents. Otherwise it falls back to the existing Azure OpenAI → OpenAI → mock chain — **zero changes needed in `agents/*.py`**. |
| `core/config.py` | Added `FOUNDRY_PROJECT_ENDPOINT`, `FOUNDRY_MODEL_DEPLOYMENT`. |
| `.env.example` | Documents the new variables and the full fallback priority order. |
| `requirements.txt` | Added optional `azure-ai-projects`, `azure-ai-agents`, `azure-identity`. |

## Provider priority order (after upgrade)

```
1. Foundry Agent Service   (FOUNDRY_PROJECT_ENDPOINT set + SDK installed)
2. Azure OpenAI             (AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_KEY set)
3. OpenAI                    (OPENAI_API_KEY set — free-tier fallback)
4. Mock                       (SENTINEL_MOCK_MODE=true or nothing configured)
```

Each tier degrades to the next automatically on missing config OR a runtime
exception (auth failure, quota, network). **The demo never breaks.**

## Foundry-native concepts now in play

- **Persistent Agents** — each Sentinel specialist (`Sentinel-ContentAgent`,
  `Sentinel-PatternAgent`, `Sentinel-KnowledgeAgent`, `Sentinel-IdentityAgent`,
  `Sentinel-JudgeAgent`) is created once via `agents.create_agent(...)` and
  cached by ID for the life of the process — this is the literal "Agent" in
  "Agent Service", visible in the Foundry portal's Agents tab.
- **Threads & Runs** — every investigation spins up a fresh `Thread` per
  agent, posts the message, and calls `runs.create_and_process(...)`. The
  full reasoning trace (messages, tool calls, tool outputs) is inspectable
  per-thread in the Foundry portal — directly supporting the "Explainable AI"
  judging criterion.
- **Function Tools** —
  - `query_threat_knowledge_base(query)` is bound to the **Knowledge Agent**.
    Its instructions require it to call this tool before answering, which is
    Sentinel's "grounded knowledge retrieval" — currently backed by
    `data/scam_kb.json`, structured so it can be swapped for an
    **Azure AI Search** index with no interface change.
  - `submit_agent_finding(...)` is bound to the **Judge Agent**, giving its
    tool-call log a structured audit trail of how it weighed each
    specialist's input — multi-step reasoning made visible.

## Setup steps (to actually run on Foundry Agent Service)

```bash
# 1. Install the SDKs
pip install azure-ai-projects azure-ai-agents azure-identity

# 2. Authenticate (DefaultAzureCredential picks this up automatically)
az login

# 3. Create / locate a Foundry project, then set:
export FOUNDRY_PROJECT_ENDPOINT="https://<your-project>.<region>.api.azureml.ms"
export FOUNDRY_MODEL_DEPLOYMENT="gpt-4o"   # your deployed model name in the project

# 4. Run normally — no other code changes needed
uvicorn api.main:app --reload --port 8000
```

On first request, watch the logs for:

```
[FoundryAgentService] Provisioned Foundry agent 'Sentinel-ContentAgent' -> asst_xxxx
[FoundryAgentService] Provisioned Foundry agent 'Sentinel-PatternAgent' -> asst_xxxx
...
[FoundryClient] FoundryLLMClient initialized — provider: foundry_agent_service
```

## Future work (post-hackathon)

1. Replace `query_threat_knowledge_base`'s JSON-file lookup with an
   **Azure AI Search** vector index (`azure-search-documents`), keeping the
   same function signature — the Knowledge Agent's tool contract doesn't
   change.
2. Move from "isolated thread per agent" to a **shared investigation
   thread** with agent hand-off, using Foundry's multi-agent orchestration
   patterns (Connected Agents) once stable in GA.
3. Persist thread IDs per investigation in Azure Table Storage so users can
   revisit the full reasoning trace for past investigations from the
   Admin/Analytics screen.
