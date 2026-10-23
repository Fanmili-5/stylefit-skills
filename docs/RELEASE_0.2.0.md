# StyleFit 0.2.0

Published as **StyleFit Skills**, formerly OwnVoice. The v0.2.0 tag and release assets retain the exact accepted commit `5a9a5db25364ccdd1d6980be03f8d7cfe7760211` and original filenames. Current repository documentation explains the new name; compatibility identifiers remain `ownvoice-*` / `ownvoice`.

OwnVoice provides four Codex skills for Python code, Chinese/English research prose, email drafts, and optional style profiles. Ordinary tasks need no profile. Samples inform expression; supplied facts, interfaces and responsibilities remain the contract.

The suite includes an offline `ownvoice verify` helper and a managed installer with a private Python runtime. Check reports distinguish passed, failed and not-run checks. A failed artifact can receive one feedback revision and must be checked again. Mechanical ledger/schema checks do not prove the truth of a prose body.

## Evidence

- 54 local software tests and four skill static validations pass.
- Frozen controlled evaluation: 12/12 OwnVoice final artifacts meet declared contracts; 5/6 paired outputs match their style samples, covering all three artifact domains.
- Eight isolated native Codex CLI acceptance cases pass.
- Actual user installation: all four skills discovered by the desktop-bundled backend, six integration cases pass mechanical checks, and one ambiguous email deadline is corrected in one feedback revision.
- Original scores, negative results and post-hoc flag-validity audit are retained. Plain prompts and full checklists also pass all final held-out contracts; no universal superiority is established.

See [evaluation](../reports/release-v02.md), [user-install validation](../reports/user-install-v02.md), and the [four-job remote CI receipt](../reports/ci-v02.md). The Linux/macOS × Python 3.9/3.12 workflow has actually passed and performs no model calls. Final release notes identify the exact final candidate commit and its CI run. Claude host invocation and independent human preference testing remain unverified.

## Install

Use Python 3.9+ from an extracted release bundle containing the helper wheel:

```sh
python3 scripts/install.py --host codex --with-tools --dry-run
python3 scripts/install.py --host codex --with-tools
```

The default is `~/.agents/skills`. See [installation](INSTALLATION.md) for upgrades, rollback, removal and offline wheels. A first installation has no earlier managed version to roll back to. Skills become available on the next turn; restart Codex if automatic discovery has not refreshed.

No samples, profiles, raw model traces or blind mappings are included in the release. No authorship/detector outcomes are promised.
