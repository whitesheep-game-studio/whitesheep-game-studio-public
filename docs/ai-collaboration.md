# Claude-led AI Engineering

Claude is the primary agent. It owns design, implementation, integration and final verification, and commits directly to `main`. Codex and Antigravity are sub-agents: Claude delegates bounded tasks to them (implementation, tests, debugging, investigation, independent review) and they report back. OWNER decides scope and approves deployment, signing, releases and permission changes.

1. Claude defines the acceptance criteria (GDD/issue), constraints and risk for each task.
2. High-risk authentication, payment, finance, PII, migration, signing and shared-engine work: a sub-agent independently assesses the design before coding.
3. Claude implements with tests, or delegates a bounded piece to Codex or Antigravity. Delegated work names the files in scope so no two agents edit the same files at once.
4. Claude checks every sub-agent result against the actual diff, acceptance criteria, security, edge cases, performance, i18n and regressions. Findings carry severity, file/line and remedy; fixes are re-checked. Sub-agent output is untrusted until verified, and no agent self-certifies.
5. Evidence: list executed unit/build/security/platform checks separately. Distinguish PASS, FAIL, NOT RUN, N/A, and scanner FINDINGS versus ERROR. No fabricated results.
6. OWNER explicitly authorizes deployments, permission changes, signing and release.

Low-risk docs/copy need no second review; normal changes are verified by Claude; high-risk changes get prior independent design review by a sub-agent. Do not edit the same files simultaneously or commit secrets. Preserve AGENTS, CLAUDE, GDD, i18n, dependency and `studio-security` rules; the stricter rule prevails. For `studio-console`, OCI RAM is 1GB: no heavy CI or extra always-on services on the server. Record evidence in `.github/pull_request_template.md`.