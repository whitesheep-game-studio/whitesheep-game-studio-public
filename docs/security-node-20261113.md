# Node.js security patch verification — 2026-11-13

Scope: reusable web workflow Node pin, web contract SDK default, README and this evidence.
Node 26.13.0 -> 26.13.1 LTS. All action SHAs, permissions, mandatory checks and other SDK pins remain unchanged.

Official release: https://nodejs.org/en/blog/release/v26.13.1
Official support schedule: https://github.com/nodejs/Release#release-schedule
Local Windows x64 ZIP verified against https://nodejs.org/dist/v26.13.1/SHASUMS256.txt:
`e2edda75bfb089654705cf65a13b58933bfd5f57148e8ebda916f58a2474f1f7`.

Common helper checks (Windows, Python 3.13.17 rather than CI's 3.15.2):
- PASS: Ruff 0.17.3 `ruff check .`.
- PASS: `python scripts/validate_workflows.py` (5 workflows, 4 starter pairs).
- PASS: actionlint 1.7.12 on all workflows and starter YAML, `-shellcheck=` (ShellCheck NOT RUN).
  Windows binary verified against upstream release checksums.
- FAIL/ENVIRONMENT ERROR: `python -m unittest discover -s tests -v`: 51 tests, 48 passed,
  3 errors from Windows denial of symlink creation (WinError 1314). No test, security rule
  or permission was changed to hide these errors. Git Bash on PATH resolves the initial
  three shell-command failures; symlink checks need a suitable environment.
- PASS: live common OSV helper: website 473 npm packages; Flutter registry packages
  67 (Kanji), 44 (Soldier), 52 (grammar), 24 (template). Private Git Pub code has no Pub advisory coverage.
- PASS: website `npm ci` and Vitest 10 tests on the verified Node 26.13.1 binary.
- PASS: website build/internal links, Python tests (2), ESLint, HTML validation,
  Prettier (local LF checkout), i18n export and structural validation (272 keys).
- PASS: Lighthouse collect/assert (2 URLs); warning thresholds retained. No public upload.
- PASS: Playwright 1.64.1 / axe desktop + mobile pilot, 18/18 tests, two workers.
  Initial runs using Python 3.13's default local HTTP backlog (5) intermittently failed
  script loads with net::ERR_CONNECTION_REFUSED. A local-only ThreadingHTTPServer
  with request_queue_size=128 and bind=127.0.0.1 passed the unchanged suite. No browser
  assertion, retry policy or production check was weakened. This is local evidence;
  the actual CI Python 3.15.2 server has not been executed here.
- NOT RUN: actual GitHub Actions, Linux runner integration, independent Claude review and deployment.

A tested local pilot does not imply all remote checks passed. Preserve the paired full
workflow/helper SHA when callers adopt this commit; keep the Pages verify/deploy gates.

## Windows symlink follow-up — 2026-11-14

Resolved the earlier three test errors. Root cause: native Windows symbolic-link
creation failed with WinError 1314 while Developer Mode was disabled and the
non-elevated process lacked SeCreateSymbolicLinkPrivilege. With explicit OWNER
approval, Developer Mode was enabled through Windows Settings (the OWNER completed
the confirmation). Registry state was verified as 1, and native file and directory
symlink creation, resolution and cleanup both passed without an elevated test process.

The three affected tests now create real temporary targets instead of assuming
Linux /tmp and /etc/hosts exist. Directory symlinks explicitly declare their type.
The release test asserts the actual link-boundary rejection message and absence of
SHA256SUMS, so an empty-artifact error cannot accidentally satisfy it. Static output
and contract tests likewise assert their intended rejection messages.

PASS: complete native Windows unittest suite, 51 tests, zero failures/errors/skips;
Ruff 0.17.3; workflow policy validation; actionlint 1.7.12 (-shellcheck=); git diff --check.
No production guard, test assertion or security check was disabled. Windows execution
uses Python 3.13.17 and Git Bash on PATH; actual GitHub Actions/Linux integration and
ShellCheck remain NOT RUN. This test/documentation-only follow-up does not require
callers to change their existing workflow/helper SHA pair.
