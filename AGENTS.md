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

## Supported runtime and dependency policy

- Before installing or upgrading a runtime, SDK or package, check its official release, support schedule, security advisories and compatibility with this repository.
- Where LTS exists, prefer the latest supported LTS with current security patches. Otherwise prefer a supported stable release. Do not assume a larger version or an older LTS is automatically safe.
- If an unresolved advisory affects the preferred version, assess actual exposure and use a supported safe alternative; record the reason and conditions for reassessment.
- Verify downloads using TLS and official checksums/signatures. If release, advisory or integrity information cannot be verified, defer the version change and report the blocker.
- Preserve existing pins, lockfiles, user changes and required checks. Authorized upgrades must update SDK/CI/dependency pins and lockfiles together in a reviewable PR and run relevant tests and representative builds.
- Record exact verified versions and lockfiles for new projects. Never install an unverified latest version on every startup or bypass a failed security/build check.
- Report local tests, remote CI, platform builds and unrun checks separately. Do not merge, deploy, publish or release without the user's explicit instruction.
