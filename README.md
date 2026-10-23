# OwnVoice Skills

The actual user installation and desktop-bundled backend checks are recorded separately in the [installation acceptance report](reports/user-install-v02.md). See the [0.2.0 release notes](docs/RELEASE_0.2.0.md) for scope and remaining validation.

Four skills for code, research writing, email and optional style profiles. Work directly without a profile, or adapt expression from confirmed samples. Keep task content and interfaces separate from style.

**0.2.0 publish-ready candidate.** The declared model and native Codex gates passed; actual results are recorded in [the 0.2 report](reports/release-v02.md). A candidate is promoted only when every declared gate passes. Historical negative results remain available: [0.1 complex diagnostic](reports/luna-v2.md), [general-use diagnostic](reports/general-v1.md).

## Install

Python 3.9+ is required for executable checks. From an extracted candidate containing the helper wheel:

```sh
python3 scripts/install.py --host codex --with-tools --dry-run
python3 scripts/install.py --host codex --with-tools
```

The Codex default is `~/.agents/skills`; use `--dest` for a chosen repository. A private versioned runtime provides the helper without changing global Python or model configuration. Existing unrelated skill directories are never overwritten. See [installation, upgrade, rollback and removal](docs/INSTALLATION.md). Claude receives portable skill directories and an explicitly unverified-host compatibility note.

When developing from source, install `requirements-dev.lock` into your chosen virtual environment and build the wheel with `python -m build --wheel --no-isolation` before using `--with-tools`. No API key or service is bundled; the helper itself makes no model calls.

## Use

- `$ownvoice-code`: generate or revise Python code using repository conventions or supplied samples; preserve public interfaces and check finite behavior.
- `$ownvoice-research`: draft or revise Chinese/English research prose from supplied sources, keeping units, unknown values and evidence scope.
- `$ownvoice-email`: draft or revise Chinese/English email, keeping current recipients, actor/action bindings and deadlines. Produces drafts only.
- `$ownvoice-profile`: explicitly create or edit an optional profile; never a prerequisite for ordinary tasks.

Example without a profile: `Use $ownvoice-code to simplify this code using the current repository conventions. Preserve its API and behavior; do not create a profile.`

Example with samples: `使用 $ownvoice-research，参考这些已确认样例的表达方式整理正文，事实只依据来源材料；不要保存档案。`

Profiles remain compatible with schema v1, scoped by domain and language. Unknown preferences remain unknown. No owner's personal defaults are built in. See [runnable examples](docs/EXAMPLES.md) and [public product scope](docs/PRODUCT_SCOPE.md).

## Checked delivery

The workflow is generate, check, revise at most once using exact feedback, and check again. Required failures or unexecuted checks are reported rather than labelled verified. Exact output schemas outrank skill defaults; natural prose is not forced into a JSON wrapper.

```sh
python3 path/to/ownvoice-email/scripts/verify.py --artifact draft.json --schema schema.json --constraints constraints.json --report checks.json
```

The installed launcher finds the isolated helper. A wheel installed in your own Python environment also supplies `ownvoice verify` / `python -m ownvoice verify`. Reports distinguish passed, failed and not_run checks; the verifier never rewrites an artifact. [Contract and exit-code documentation](docs/VERIFICATION.md) explains supported checks and their limits. A correct ledger does not establish that the body says the same thing, and recorded model review is not mechanical proof.

## Development and release

```sh
python -m pip install -r requirements-dev.lock
python -m unittest discover -s tests
python scripts/check_bundle.py
python scripts/release_audit.py
python -m build --wheel --no-isolation
python scripts/package_release.py --channel candidate
python scripts/verify_distribution.py
```

Public CI covers Linux/macOS and Python 3.9/3.12 without paid model calls. Native Codex tests, model experiments and public CI execution are distinct evidence layers. All current experimental generation and grading explicitly select `gpt-6-luna / medium`; raw response metadata may not report the model identity.

The 0.2 round has an independent 120-CLI-task cap on top of 239 preserved jobs; failures, revisions, grading and native jobs count. Do not reset the ledger. Inputs are frozen before formal evaluation. Raw artifacts, mappings and personal data remain under ignored `.local/`. The release builder uses `release-files.json`, adds the audited helper wheel and hashes every archive entry. `--channel release` requires passing gates and matching tested product hashes.

No GitHub publication occurs automatically. No authorship, detector, universal style-match, general code-equivalence or human-preference guarantee is made.

[中文说明](README.zh-CN.md)
