# WhiteSheep Dual-AI Peer Engineering

Codex and Claude are equal engineers and independently review each other's work. They both may design, code, debug, test and document. Assign A to implement, B to review the PR; alternate per task. OWNER retains priorities and final decision for merge, deployment, release and security.

1. Define issue and acceptance criteria; respect repository AGENTS, CLAUDE, project/GDD/i18n and security policy.
2. High-risk authentication, purchases, finances, PII, production migrations and shared framework work require both agents to critique design *before* implementation.
3. A develops in isolated branch and supplies tests and PR. B reviews actual diff, requirements, edge cases, security, performance, i18n, accessibility, regressions without simply trusting A's description.
4. B records severity, file/line, reproduction and correction. A fixes; B re-reviews. Disputes require primary spec, reproducible tests or measurement; unresolved tradeoffs go to OWNER.
5. Record test runs separately as PASS, FAIL, NOT RUN, N/A; for scanners use FINDINGS and ERROR. Never invent CI results or count AI self-review as independent.
6. Only OWNER explicitly authorizes merge, deployment, signing, release, permissions or production operations.

Low-risk documentation can use one engineer plus checks; normal feature requires peer review; high-risk features require independent design check and stricter tests. Keep branches separate, no simultaneous edits or committed secrets. Heavy CI does not run on 1GB OCI studio-console. Record evidence in `.github/pull_request_template.md`.
