# StyleFit 0.2.0 public release verification

StyleFit Skills is the public name of the project previously called OwnVoice. The repository and release title changed; version 0.2.0 retains the accepted source commit, all six asset bytes, `ownvoice-*` skill names and `ownvoice` helper. Documentation on the default branch records the rename after the frozen release commit.

- [Public repository](https://github.com/Fanmili-5/stylefit-skills)
- [Published release and downloads](https://github.com/Fanmili-5/stylefit-skills/releases/tag/v0.2.0)
- Accepted/tagged source: `5a9a5db25364ccdd1d6980be03f8d7cfe7760211`.
- ZIP SHA-256: `2c0abf855f50641d194df78e0b372bfd43ee6a2e5d93a81fc3472d89d180bac0`.

## Checks performed after publication

1. GitHub's public REST endpoints returned the public repository, published non-prerelease, and exact accepted tag commit without an Authorization header or GitHub credentials.
2. All six release assets were downloaded using anonymous HTTPS requests. Each matched the accepted local SHA-256 and GitHub asset digest. Every `SHA256SUMS` entry passed.
3. The ZIP's complete file set matched its 130-file manifest, and every entry hash passed.
4. In a new temporary directory, the distributed installer completed its dry run, then installed four skills and a private runtime. Python dependencies came from the public PyPI index with pip configuration and cache disabled; no local wheelhouse was supplied.
5. Every installed skill file matched the downloaded source. The installed helper accepted a conforming JSON artifact and rejected a renamed required field with exit code 1. Uninstall removed the four managed aliases.
6. The distribution acceptance runner was executed against the anonymously downloaded ZIP: all 54 software tests, skill validation and 11 distribution checks passed, including real runtime upgrade, rollback and removal. The maintenance upgrade uses the same product payload under a synthetic version label and does not establish arbitrary cross-version compatibility.

The earlier [four-job Linux/macOS × Python 3.9/3.12 CI](https://github.com/Fanmili-5/stylefit-skills/actions/runs/39926804859) applies to the exact accepted release commit. [Real user Codex discovery/invocation evidence](user-install-v02.md) and [frozen model results](release-v02.md) remain separate. This publication verification added **zero model calls**; the 0.2 ledger remains 117/120.

This anonymous-install check ran on one local macOS host. It establishes the public download and clean install path in that environment; it is not a session run by an independent external user. Desktop picker clicks and Claude host invocation remain unverified.

## 安装

下载 Release 页的 `ownvoice-skills-0.2.0.zip` 并校验；GitHub 自动生成的 Source code 压缩包不含辅助 wheel。解压后进入 `ownvoice-skills`，使用 Python 3.9+ 执行：

```sh
python3 scripts/install.py --host codex --with-tools --dry-run
python3 scripts/install.py --host codex --with-tools
```

完整下载命令见[中文说明](../README.zh-CN.md)。公开名称为 StyleFit，0.2.0 的调用入口仍为 `$ownvoice-code`、`$ownvoice-research`、`$ownvoice-email`、`$ownvoice-profile`，现有安装无须迁移。

Machine-readable checks: [public-release-v02.json](public-release-v02.json).
