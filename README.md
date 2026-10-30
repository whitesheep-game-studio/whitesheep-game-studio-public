# WhiteSheep common CI foundation

Reusable Flutter, Godot, static web and Python CLI verification for
`whitesheep-game-studio/whitesheep-game-studio-public`. This public repository contains
generic automation, fixtures and configuration examples. Product code, private game data
and credentials belong in their own repositories. Product adoption requires a tested
workflow commit and real platform pilots; helper unit tests alone do not verify game builds.

The repository name `.github` is only required for organization starter templates.
Reusable workflows themselves can live in another repository's `.github/workflows/`.
This public repository lets both public and private projects call the same workflow.
No existing private repository needs to be made public.

## Contract and profiles

Each caller adds `.ci/project.yml`; see `examples/`. Required common fields:

- `version: 1`, `stack`, `directory`, `kind: application|library|tool`, `build`.
- `data.commands`: existing data validators, or `data.reason` for no additional product data.
- `i18n`: actual resources for applications; a justified `format: none` for tools/libraries without UI.
- `dependencies`: resolved lockfiles, or a justified dependency-free Godot/Python profile.
- `checks`: existing commands for Godot, web and Python; preserve their assertions and coverage.

| Profile | Required checks | Build |
|---|---|---|
| Flutter | exact .fvmrc, frozen pub, Dart format, analyze, test, data, ARB, OSV | Android debug for apps; none for libraries |
| Godot | .godot-version 4.6.3, SHA-512 engine/templates, existing import/parser/scene/boot checks, data, CSV/PO | unsigned Windows debug, actual preset and nonempty exe |
| Web | Node 22, npm ci, explicit existing build/lint/format/unit/browser/axe/HTML/Lighthouse commands, data, exported JSON locale dictionaries, OSV | existing static build; deployment stays in caller |
| Python | Python 3.12, Ruff E4/E7/E9/F, pinned requirements, existing tests/data, optional applicable locales, OSV | none for current CLI tools |

Current profiles do **not** implement iOS/macOS/Flutter desktop, Godot Android,
FastAPI/PostgreSQL/Docker or an all-platform tag release pipeline. Add a profile only
after actual project requirements and pilot validation. `prepare_release.py` prepares
local SHA-256 checksums/notes for existing artifacts; it publishes nothing.

Applications with missing locale resources or export/build configuration fail preflight.
Existing applications need actual UI-connected resource migration before adopting this contract.
Do not add fictitious resources simply to satisfy the validator.

## Locale format support

- Supported locales: exactly `ko`, `ja`, `en`, explicit base and fallback; both must exist.
- ARB: duplicate JSON keys, locale, full matching keys, metadata/placeholder consistency;
  recursive named/simple ICU, plural, select and selectordinal parsing with `other`.
  Date/number skeletons and ICU apostrophe escaping fail explicitly until covered by a dedicated adapter.
- Godot CSV: `keys,ko,ja,en` header (column order may vary), strict rows, duplicate/missing keys,
  nonempty values and named `{placeholders}`.
- PO: Language metadata, duplicate entries, matching keys and named placeholders;
  fuzzy/context/plural entries require an adapter and fail explicitly.
- Web: per-locale strict JSON dictionaries exported from actual source before validation.
  JavaScript source is **not** regex-parsed or executed by the generic parser. The website needs
  its own tested exporter and a reviewed missing-key migration. Keep its Korean legal fallback.

These are structural checks; they do not review translation wording or rewrite fallback policy.
WSDS (`design-system`) remains the owner of common glossary and i18n policy.

## Security and costs

- Actions are full-SHA pinned; permissions `contents: read`; no inherited secrets or publication credentials.
- All caller code is ordinary untrusted PR code. Never elevate it to `pull_request_target`.
- OSV queries all resolved registry packages in supported pub/npm/flattened exact PyPI locks;
  advisory findings, malformed responses and service/network failures fail CI. No allowlist/ignore bypass.
- Git Pub dependencies must have a full resolved commit; OSV does not cover private Git code.
  Their review/auth must be handled separately before adopting Kanji. Local/path packages are rejected.
- `format: none` checks for requirements/addons in current Godot/Python profiles, but does not claim
  generic source-level vulnerability coverage. Godot addons need their own inventory adapter.
- Single Linux job per profile, timeouts 10–25 minutes, Flutter SDK cache, npm cache keyed by lockfile,
  result/build artifacts retained 3 days. No cron, whole-engine matrices or store uploads.
- Summary records actual job status even on failure. Required commands keep their original exit code.
  Callers must preserve branch-protection check names and gate deployments on the full verification job.

## Publish and adopt

1. Review the foundation PR in this repository.
2. Run `validate-workflows.yml` on that PR. This checks helpers, fixtures and YAML, **not platform builds**.
3. Review callers' existing tests, source pins, locale resources and export/build settings first.
4. After review, use the tested destination commit in both starter `uses: ...@SHA` and
   `with.automation-ref: SHA`. `REPLACE_WITH_TESTED_HUB_SHA` is intentionally not runnable.
   Test a real caller on that SHA before broadly adopting or tagging a release.
5. Private caller access and cross-repository dependency credentials need separate verification.
   Public website callers cannot use a private common workflow repository.
6. Preserve existing `check`/`verify` protection checks with stable aggregator jobs where necessary.
   The reusable job's nested name may differ. Keep website Pages upload/deploy gated in the caller;
   this foundation never deploys Pages. Do not replace its workflow blindly.

The workflow and helper SHA inputs must match. A reusable workflow's relative paths
refer to the caller checkout, so helpers are explicitly checked out separately under `automation/`;
the caller is under `project/`. Product format/lint globs cannot accidentally include helper code.

## Local validation

```sh
python -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/ruff check .
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/validate_workflows.py
bash scripts/install_actionlint.sh /tmp/studio-actionlint
/tmp/studio-actionlint/actionlint -shellcheck= .github/workflows/*.yml workflow-templates/*.yml
```

If a development network blocks `api.osv.dev`, that is a failed local live
audit, not a clean dependency result; the GitHub Actions audit must pass before merge.
Never replace that audit with mocks in production. Unit tests deliberately mock clean,
vulnerable, partial and unavailable API results to test failure handling.
