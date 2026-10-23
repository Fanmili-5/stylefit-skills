# StyleFit 0.2.1

This maintenance release unifies the four public skill names and their UI labels:

- `StyleFit-code` → `$stylefit-code`
- `StyleFit-research` → `$stylefit-research`
- `StyleFit-email` → `$stylefit-email`
- `StyleFit-profile` → `$stylefit-profile`

The wheel/archive package is `stylefit-skills`. The executable helper is `stylefit verify`; `python -m stylefit verify` is also supported. Skill descriptions, task workflows and verification rules are unchanged apart from naming/version metadata.

## Install or upgrade

Download the **release asset** `stylefit-skills-0.2.1.zip`, verify its SHA-256, extract it and enter `stylefit-skills`. Python 3.9+ and macOS/Linux are supported.

```sh
# New installation
python3 scripts/install.py --host codex --with-tools
# Existing managed 0.2.0 installation
python3 scripts/install.py --host codex --with-tools --upgrade
```

Use `--dry-run` to preview. The upgrade replaces the four old managed aliases with `stylefit-*`; no duplicate skill entries remain. The new installer's `--rollback` restores the prior runtime and names. Existing unrelated directories and edited installed skills are preserved by refusing the operation. The internal `.ownvoice` store and Python modules remain for compatibility.

[58 software tests, four static skill validations, real runtime migration and desktop backend discovery](../reports/naming-v021.md) pass. No model evaluation was rerun: historical 0.2.0 scores remain unchanged. No new authorship, detector or general-quality claim is made. The 0.2.0 release remains available with its original assets and checksums.
