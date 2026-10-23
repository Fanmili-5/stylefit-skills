# Installation, upgrade and rollback

Python 3.9+ is required for the optional verification runtime. The release candidate contains four regular skill directories and a helper wheel. Existing Codex authentication is used only when the user invokes Codex; the helper itself has no API client, background service or key requirement.

## Recommended Codex installation

From an extracted release bundle:

```sh
python3 scripts/install.py --host codex --with-tools --dry-run
python3 scripts/install.py --host codex --with-tools
```

The default skill directory is `~/.agents/skills`. Use `--dest /chosen/project/.agents/skills` for a repository-level install. The installer maintains versioned files and an isolated runtime in the sibling `.ownvoice` directory, with skill aliases referring through one `current` link. It never overwrites an unrelated existing directory and does not modify global Python, model settings or authentication.

Dependencies are installed using `requirements-runtime.lock`. An existing offline wheel collection can be supplied with `--wheelhouse /path/to/wheels`; the collection must match the installation platform and Python version. Without this option, pip uses its configured package source. An explicit helper wheel may be supplied with `--wheel`.

The old preview used `~/.codex/skills`. This installer does not delete or silently migrate legacy copies. If both locations contain the same skill name, inspect and remove the copy you no longer want to use. The default installation and repository-scoped aliases are validated separately from generated-artifact quality.

## Maintenance

```sh
python3 scripts/install.py --host codex --with-tools --upgrade
python3 scripts/install.py --host codex --rollback --dry-run
python3 scripts/install.py --host codex --rollback
python3 scripts/install.py --host codex --uninstall
```

Upgrade stages a complete new version before switching the shared link; setup failures leave the previous active version unchanged. Rollback switches back to the previous managed release. Reinstalling the identical release is idempotent. Modified installed skill files cause a refusal rather than destruction; preserve your edits in a separate skill or checkout first.

A first installation has no earlier managed version to restore. Installed skills are available on the next turn. Codex normally detects changes automatically; restart it if discovery has not refreshed.

Uninstall removes only the managed skill aliases. Cached releases remain for recovery and are not private profile storage. User-created profiles and samples are never deleted. The installer does not support merging two users' skill directories or importing arbitrary existing folders as owned releases.

## Portable use and Claude

Each skill directory can also be copied to a compatible host and contains its own instructions, references and launcher. Install the Python wheel in that host's chosen Python environment if executable verification is wanted, or report checks as unavailable. Do not advertise full verification when only Markdown was copied.

Claude receives the same portable directories, but actual Claude discovery and invocation are not part of the 0.2 Codex-first acceptance. No Claude model runs are used. macOS native Codex acceptance and Linux/macOS Python CI are different evidence layers; a configured CI matrix is not an executed remote CI result.
