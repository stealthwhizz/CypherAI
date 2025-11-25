# CypherAI Workflow Diagram

## Complete System Flowchart

```mermaid
flowchart TD
    Start([Developer Creates Pull Request]) --> Trigger[GitHub Actions Triggered]
    Trigger --> Init[Initialize CypherAI Scanner]
    Init --> DetectFiles[Detect Changed Files in PR]
    
    DetectFiles --> RootOrch[Root Orchestrator Agent<br/>Gemini 1.5 Pro]
    
    RootOrch --> ParallelStart{Parallel Agent<br/>Execution}
    
    %% Parallel Agent Execution
    ParallelStart -->|Thread 1| SecAgent[Security Scanner Agent<br/>Gemini 1.5 Flash]
    ParallelStart -->|Thread 2| CompAgent[Compliance Enforcer Agent<br/>Gemini 1.5 Flash]
    ParallelStart -->|Thread 3| PerfAgent[Performance Monitor Agent<br/>Gemini 1.5 Flash]
    ParallelStart -->|Thread 4| PolAgent[Policy Engine Agent<br/>Gemini 1.5 Flash]
    
    %% Security Scanner Flow
    SecAgent --> SecTools[Run Security Tools]
    SecTools --> Bandit[Bandit: SAST Analysis]
    SecTools --> Safety[Safety: Dependency Scan]
    SecTools --> Trivy[Trivy: Container Scan]
    Bandit --> SecFindings[Security Findings]
    Safety --> SecFindings
    Trivy --> SecFindings
    
    %% Compliance Enforcer Flow
    CompAgent --> CompCheck[Check Compliance Standards]
    CompCheck --> PCI[PCI DSS Validation]
    CompCheck --> SOC2[SOC 2 Validation]
    CompCheck --> HIPAA[HIPAA Validation]
    CompCheck --> GDPR[GDPR Validation]
    PCI --> CompFindings[Compliance Findings]
    SOC2 --> CompFindings
    HIPAA --> CompFindings
    GDPR --> CompFindings
    
    %% Performance Monitor Flow
    PerfAgent --> PerfCheck[Detect Performance Issues]
    PerfCheck --> NPlusOne[N+1 Query Detection]
    PerfCheck --> MemLeak[Memory Leak Detection]
    PerfCheck --> Blocking[Blocking Operation Detection]
    NPlusOne --> PerfFindings[Performance Findings]
    MemLeak --> PerfFindings
    Blocking --> PerfFindings
    
    %% Policy Engine Flow
    PolAgent --> LoadState[Load Historical State]
    LoadState --> DevPattern[Analyze Developer Patterns]
    DevPattern --> AdaptSev[Adaptive Severity Scoring]
    AdaptSev --> PolFindings[Policy Findings]
    
    %% Aggregation
    SecFindings --> Aggregate[Root Orchestrator<br/>Aggregates All Findings]
    CompFindings --> Aggregate
    PerfFindings --> Aggregate
    PolFindings --> Aggregate
    
    Aggregate --> RiskCalc[Calculate Risk Score<br/>0-100]
    
    RiskCalc --> Decision{Risk Score<br/>Evaluation}
    
    Decision -->|Score >= 70| Block[❌ BLOCK MERGE]
    Decision -->|Score < 70 AND<br/>Critical Issues| Block
    Decision -->|Score < 70 AND<br/>No Critical Issues| Approve[✅ APPROVE MERGE]
    
    Block --> PostComment1[Post PR Comment<br/>with Findings]
    Approve --> PostComment2[Post PR Comment<br/>with Summary]
    
    PostComment1 --> GenReport[Generate Audit Report]
    PostComment2 --> GenReport
    
    GenReport --> SaveState[Policy Engine<br/>Saves Learning State]
    
    SaveState --> End([Scan Complete<br/>0.75s Average])
    
    %% Styling
    classDef orchClass fill:#9333ea,stroke:#7c3aed,color:#fff
    classDef agentClass fill:#3b82f6,stroke:#2563eb,color:#fff
    classDef toolClass fill:#10b981,stroke:#059669,color:#fff
    classDef decisionClass fill:#f59e0b,stroke:#d97706,color:#fff
    classDef resultClass fill:#ef4444,stroke:#dc2626,color:#fff
    classDef approveClass fill:#22c55e,stroke:#16a34a,color:#fff
    
    class RootOrch,Aggregate orchClass
    class SecAgent,CompAgent,PerfAgent,PolAgent agentClass
    class Bandit,Safety,Trivy,PCI,SOC2,HIPAA,GDPR,NPlusOne,MemLeak,Blocking toolClass
    class Decision,ParallelStart decisionClass
    class Block resultClass
    class Approve approveClass
```

## Simplified User Journey

```mermaid
flowchart LR
    A[👨‍💻 Developer<br/>Pushes Code] --> B[🤖 GitHub Actions<br/>Auto-Triggers]
    B --> C[🧠 4 AI Agents<br/>Scan in Parallel<br/>0.75 seconds]
    C --> D{Risk Score<br/>Analysis}
    D -->|High Risk| E[❌ Block Merge<br/>+ Detailed Report]
    D -->|Low Risk| F[✅ Approve Merge<br/>+ Summary]
    E --> G[📊 Audit-Ready<br/>Reports]
    F --> G
    G --> H[💾 Learn from<br/>Developer Patterns]
    
    style A fill:#3b82f6,stroke:#2563eb,color:#fff
    style B fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style C fill:#ec4899,stroke:#db2777,color:#fff
    style D fill:#f59e0b,stroke:#d97706,color:#fff
    style E fill:#ef4444,stroke:#dc2626,color:#fff
    style F fill:#22c55e,stroke:#16a34a,color:#fff
    style G fill:#06b6d4,stroke:#0891b2,color:#fff
    style H fill:#a855f7,stroke:#9333ea,color:#fff
```

## Multi-Agent Collaboration Detail

```mermaid
flowchart TD
    PR[Pull Request] --> Root[Root Orchestrator<br/>Analyzes Context]
    
    Root --> Par{Parallel<br/>Execution}
    
    Par --> Sec[🔒 Security Scanner<br/>OWASP Top 10]
    Par --> Comp[📋 Compliance Enforcer<br/>PCI/SOC2/HIPAA]
    Par --> Perf[⚡ Performance Monitor<br/>Query/Memory/Blocking]
    Par --> Pol[🧠 Policy Engine<br/>Adaptive Learning]
    
    Sec --> Share[Agent Communication<br/>Share Findings]
    Comp --> Share
    Perf --> Share
    Pol --> Share
    
    Share --> CrossDomain[Cross-Domain Intelligence]
    
    CrossDomain --> Example1["Example: SQL Injection Found<br/>↓<br/>Compliance: PCI DSS 6.5.1 Violation<br/>↓<br/>Performance: Check Query Efficiency<br/>↓<br/>Policy: Developer Usually Fixes SQL"]
    
    Example1 --> Decision[Intelligent Context-Aware<br/>Merge Decision]
    
    Decision --> Output[PR Comment + Report + Learning]
    
    style Root fill:#9333ea,stroke:#7c3aed,color:#fff
    style Sec fill:#ef4444,stroke:#dc2626,color:#fff
    style Comp fill:#3b82f6,stroke:#2563eb,color:#fff
    style Perf fill:#f59e0b,stroke:#d97706,color:#fff
    style Pol fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style CrossDomain fill:#ec4899,stroke:#db2777,color:#fff
    style Decision fill:#22c55e,stroke:#16a34a,color:#fff
```

## Adaptive Learning Flow

```mermaid
flowchart LR
    Scan1[Scan #1<br/>Detects 10 Issues] --> State1[Policy Engine<br/>Records Patterns]
    
    State1 --> Scan2[Scan #2<br/>Developer Fixes<br/>Auth Issues Fast]
    
    Scan2 --> State2[Policy Engine<br/>Updates Trust Score]
    
    State2 --> Scan3[Scan #50<br/>Adaptive Scoring Active]
    
    Scan3 --> Result[60% Fewer<br/>False Positives]
    
    State1 -.->|Learns| Pattern["Developer Patterns:<br/>✓ Always fixes auth<br/>✗ Ignores warnings<br/>⚡ Fast SQL fixes"]
    
    Pattern -.->|Informs| Scan3
    
    style Scan1 fill:#3b82f6,stroke:#2563eb,color:#fff
    style State1 fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style Scan2 fill:#3b82f6,stroke:#2563eb,color:#fff
    style State2 fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style Scan3 fill:#3b82f6,stroke:#2563eb,color:#fff
    style Result fill:#22c55e,stroke:#16a34a,color:#fff
    style Pattern fill:#ec4899,stroke:#db2777,color:#fff
```

---

## How to Use These Diagrams

### For Kaggle Submission
1. **Take screenshots** of the rendered Mermaid diagrams above
2. **Use as thumbnail**: The "Multi-Agent Collaboration Detail" diagram works great
3. **Include in presentation**: Shows technical sophistication visually

### To Render in GitHub
- Copy this file to your GitHub repo
- GitHub automatically renders Mermaid diagrams in markdown files
- View at: https://github.com/stealthwhizz/CypherAI/blob/main/WORKFLOW_DIAGRAM.md

### To Generate PNG Images
Use one of these tools:
1. **Mermaid Live Editor**: https://mermaid.live/
   - Paste code → Copy PNG/SVG
2. **GitHub**: Push this file, GitHub renders it, take screenshot
3. **VS Code Extension**: Install "Markdown Preview Mermaid Support"
4. **Online Tools**: https://mermaid.ink/ (direct PNG export)

---

## Diagram Explanations

### Complete System Flowchart
Shows end-to-end flow from PR creation → GitHub Actions → parallel agent execution → risk calculation → merge decision. Includes all 4 agents and their specific tools.

### Simplified User Journey
High-level view for non-technical audiences. Shows developer experience in 8 simple steps.

### Multi-Agent Collaboration Detail
Highlights the key innovation: how agents share findings and create cross-domain intelligence that single-AI systems cannot achieve.

### Adaptive Learning Flow
Demonstrates how Policy Engine learns over time, reducing false positives from Scan 1 → Scan 50.

---

**Best for Kaggle Thumbnail**: Multi-Agent Collaboration Detail (shows innovation clearly)

**Best for Technical Presentation**: Complete System Flowchart (shows full architecture)

**Best for Business Audience**: Simplified User Journey (easy to understand value)
