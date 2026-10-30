# Common CI development rules

- Read README.md, the caller contract and the caller's existing checks before changing a profile.
- Preserve product tests, locale/fallback policy, SDK pins, required check names and deployment gates.
- Run `python -m unittest discover -s tests -v`, `ruff check .`,
  `python scripts/validate_workflows.py` and actionlint on workflows and starters.
- Add regression fixtures when changing parsers, exit handling or dependency formats. Include failure cases.
- Pin third-party Actions by full SHA; SDK changes require official checksums and a real pilot build.
- Missing resources, empty suites, advisory API failures and engine errors must not become green checks.
- UI localization belongs to the product; WSDS owns common terminology. Structural checks do not approve translations.
- Never add secrets, `pull_request_target`, blanket secret inheritance, automatic merge or store publication.
- Caller source runs with read-only permissions and no privileged credentials. Private cross-repo dependencies
  require a separately reviewed least-privilege auth design; never inject credentials into fork code.
- Reusable workflow refs and helper checkout refs must point to the same tested full SHA.
- Report local tests, actual Actions, platform builds and publication status separately. If central publication
  or access is blocked, report the concrete error and retain a reviewable PR without claiming activation.
