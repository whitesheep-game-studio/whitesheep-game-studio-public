# Claude-led Engineering

Read `AGENTS.md` and `docs/ai-collaboration.md`. Claude is the primary agent: it designs, implements, integrates, does the final verification and commits directly to `main`. Codex and Antigravity are sub-agents that take delegated work (implementation, tests, investigation, independent review) and report to Claude; verify their results against the actual diff and tests. Respect existing security, GDD, i18n and dependency policies. No concurrent edits of the same files, fabricated test outcomes, secrets, or unapproved deployment, release or permission changes.
