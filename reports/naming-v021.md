# StyleFit 0.2.1 naming and migration acceptance

All public entry points now use one prefix:

| Display name | Invocation / folder |
|---|---|
| StyleFit-code | `stylefit-code` |
| StyleFit-research | `stylefit-research` |
| StyleFit-email | `stylefit-email` |
| StyleFit-profile | `stylefit-profile` |

The package is `stylefit-skills`, the helper is `stylefit verify`, and `python -m stylefit verify` works. Internal `ownvoice` Python modules and the `.ownvoice` release store remain implementation details so existing runtime paths and rollback stay valid.

## Verification

- All 58 software tests pass, including legacy-name migration, collision preservation, edited-skill protection and recovery from a state-write failure in both upgrade and rollback directions.
- Four official skill-creator static checks and the bundle check pass.
- The extracted 0.2.1 candidate passes 11 real-runtime distribution checks, including installation, maintenance upgrade, rollback and uninstall.
- A fresh real 0.2.0 installation from its accepted ZIP was upgraded to 0.2.1, rolled back to old names/runtime, then returned to new names/runtime. Both the `stylefit` command and Python module execute verification. Twelve migration steps pass.
- The current user installation was upgraded. Desktop-bundled Codex discovers all four new names, enabled, with the expected `StyleFit-*` display names and zero discovery errors. No old OwnVoice entries remain. Configuration and other skill entrypoints are unchanged.
- All 18 skill files were compared with the accepted 0.2.0 ZIP. Differences are limited to identifiers, headings, display metadata and version numbers. Verification, profile-selection and code-checking implementations and runtime dependency lock are byte-identical.

The formal 0.2.0 results remain historical evidence, not a new 0.2.1 quality measurement. No model calls were added; the ledger remains 117/120. Backend discovery does not establish desktop UI clicks or independent user experience. Claude remains unverified. Historical evaluation scripts/IDs retain their original names; reproduce that experiment from the v0.2.0 tag.

See [machine-readable evidence and product hashes](naming-v021.json), [installation/migration](../docs/INSTALLATION.md) and [release notes](../docs/RELEASE_0.2.1.md). Final distribution hashes and CI links are attached to the GitHub release.
