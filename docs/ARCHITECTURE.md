# Sentinel AI — Architecture

## High-Level System Flow

```mermaid
flowchart TD
    U[User] -->|Suspicious message<br/>email / SMS / WhatsApp / URL| GW[Investigation Gateway<br/>FastAPI]

    GW --> ORCH[Orchestrator Agent<br/>core/orchestrator.py]

    ORCH -->|parallel dispatch| CA[Content Agent<br/>Linguistic & psychological analysis]
    ORCH -->|parallel dispatch| PA[Pattern Agent<br/>Scam template matching]
    ORCH -->|parallel dispatch| KA[Knowledge Agent<br/>Foundry knowledge retrieval]
    ORCH -->|parallel dispatch| IA[Identity Agent<br/>Sender authenticity]

    CA --> JA[Judge Agent<br/>Evidence aggregation & verdict]
    PA --> JA
    KA --> JA
    IA --> JA

    JA --> REPORT[Scam Risk Report]

    REPORT --> SCORE[Risk Score 0-100]
    REPORT --> VERDICT[Verdict<br/>SCAM / SUSPICIOUS / SAFE]
    REPORT --> EVID[Evidence]
    REPORT --> REC[Recommendations]

    REPORT --> UI[Frontend<br/>Next.js + Fluent UI]
    UI --> U

    KA -.->|grounding| AIS[(Azure AI Search /<br/>Sentinel Threat KB)]
    CA -.-> FOUNDRY{{Microsoft Foundry<br/>Agent Service}}
    PA -.-> FOUNDRY
    KA -.-> FOUNDRY
    IA -.-> FOUNDRY
    JA -.-> FOUNDRY

    style FOUNDRY fill:#5FE3D0,stroke:#0A0E1A,color:#0A0E1A
    style JA fill:#F2A93B,stroke:#0A0E1A,color:#0A0E1A
    style ORCH fill:#141C2F,stroke:#5FE3D0,color:#E9EDF7
```

## Multi-Agent Reasoning Sequence

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant GW as Investigation Gateway
    participant ORCH as Orchestrator
    participant CA as Content Agent
    participant PA as Pattern Agent
    participant KA as Knowledge Agent
    participant IA as Identity Agent
    participant JA as Judge Agent
    participant FOUNDRY as Microsoft Foundry

    User->>GW: POST /api/investigate/stream { text }
    GW->>ORCH: investigate_stream(text)

    par Parallel agent dispatch
        ORCH->>CA: analyze(text)
        CA->>FOUNDRY: reasoning completion
        FOUNDRY-->>CA: risk_score, evidence, reasoning
        CA-->>ORCH: AgentResult
    and
        ORCH->>PA: analyze(text)
        PA->>FOUNDRY: reasoning completion
        FOUNDRY-->>PA: risk_score, evidence, templates
        PA-->>ORCH: AgentResult
    and
        ORCH->>KA: analyze(text)
        KA->>KA: query Sentinel threat KB
        KA->>FOUNDRY: reasoning over KB results
        FOUNDRY-->>KA: risk_score, campaign match
        KA-->>ORCH: AgentResult
    and
        ORCH->>IA: analyze(text)
        IA->>FOUNDRY: reasoning completion
        FOUNDRY-->>IA: risk_score, spoofing signals
        IA-->>ORCH: AgentResult
    end

    ORCH-->>GW: SSE agent_completed x4
    GW-->>User: stream agent results live

    ORCH->>JA: run(text, all_agent_results)
    JA->>FOUNDRY: weigh evidence, resolve disagreements
    FOUNDRY-->>JA: final_score, verdict, recommendations
    JA-->>ORCH: InvestigationReport

    ORCH-->>GW: SSE investigation_complete
    GW-->>User: final Scam Risk Report
```

## Repository Structure

```
sentinel-ai/
├── agents/                  # Specialist reasoning agents
│   ├── content_agent.py     # Linguistic & psychological analysis
│   ├── pattern_agent.py      # Scam template & structural matching
│   ├── knowledge_agent.py     # Threat intelligence retrieval
│   ├── identity_agent.py      # Sender authenticity verification
│   └── judge_agent.py          # Final arbiter & verdict generation
│
├── core/                     # Orchestration & Foundry abstraction
│   ├── config.py             # Shared models, enums, config
│   ├── foundry_client.py      # Foundry / Azure OpenAI / mock LLM client
│   ├── foundry_agent_service.py  # Microsoft Foundry Agent Service (threads/tools)
│   └── orchestrator.py         # Parallel agent dispatch + SSE streaming
│
├── api/
│   └── main.py               # FastAPI gateway (REST + SSE)
│
├── data/
│   └── scam_kb.json           # Sentinel threat intelligence knowledge base
│
├── frontend/                  # Next.js + TypeScript + Tailwind UI
│   └── src/
│       ├── app/page.tsx        # Landing + investigation + live reasoning + verdict
│       ├── components/         # AgentNetworkDiagram, RiskGauge, VerdictReport
│       └── lib/                 # Types & SSE API client
│
├── docs/                       # Architecture, demo script, submission assets
├── deploy/                      # Azure deployment scripts & Dockerfiles
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```
