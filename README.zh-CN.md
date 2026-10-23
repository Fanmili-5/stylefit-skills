# StyleFit Skills

**StyleFit** 意为“让表达适配风格”，原名 OwnVoice。0.2.1 统一使用 `stylefit-具体领域` 作为目录和调用名，界面显示 `StyleFit-具体领域`；安装包为 `stylefit-skills`，辅助命令为 `stylefit verify`。

面向所有使用者的四技能套件：代码、科研文字、邮件，以及可选风格档案。不提供档案也能直接使用；提供确认样例时，只参考表达习惯，事实和功能约束仍以任务为准。

**[0.2.1 命名统一版](https://github.com/Fanmili-5/stylefit-skills/releases/tag/v0.2.1)。** 0.2.0 的模型与 Codex 宿主门槛已通过。[验收报告](reports/release-v02.md) 记录实际结果。此前[复杂诊断的负面结果](reports/luna-v2.md)和[通用适配结果](reports/general-v1.md)继续保留。

命名统一、升级和安装结果详见[0.2.1 验证记录](reports/naming-v021.md)。

## 安装与维护

需要 macOS 或 Linux、Python 3.9+。下载下方发布附件；GitHub 自动生成的 “Source code” ZIP 不含辅助 wheel。在空目录中执行：

```sh
curl -fLO https://github.com/Fanmili-5/stylefit-skills/releases/download/v0.2.1/stylefit-skills-0.2.1.zip
curl -fLO https://github.com/Fanmili-5/stylefit-skills/releases/download/v0.2.1/stylefit-skills-0.2.1.zip.sha256
# macOS；Linux 改用 sha256sum -c stylefit-skills-0.2.1.zip.sha256
shasum -a 256 -c stylefit-skills-0.2.1.zip.sha256
unzip stylefit-skills-0.2.1.zip
cd stylefit-skills
```

预览后安装四个技能和独立辅助环境：

```sh
python3 scripts/install.py --host codex --with-tools --dry-run
python3 scripts/install.py --host codex --with-tools
```

已有 OwnVoice 受管安装时，为安装命令增加 `--upgrade`；旧入口会换成新入口，回滚则恢复对应旧名。用户自建同名目录或改过的技能会触发拒绝覆盖。

默认安装到 `~/.agents/skills`，也可用 `--dest` 指定项目目录。辅助工具运行在独立版本环境中，不改全局 Python、模型配置或认证，不覆盖用户已有的不同技能。

安装后在下一条消息中使用 `$stylefit-code` 等入口；若自动发现未刷新，可重启 Codex。[当前用户目录实测记录](reports/user-install-v02.md)与原隔离宿主验收分开保存。

```sh
python3 scripts/install.py --host codex --with-tools --upgrade
python3 scripts/install.py --host codex --rollback
python3 scripts/install.py --host codex --uninstall
```

卸载只移除本工具管理的技能链接，保留缓存版本及用户档案。完整规则、离线依赖选项和 Claude 便携目录的验证边界见[安装说明](docs/INSTALLATION.md)。源码使用者先在选定虚拟环境安装 `requirements-dev.lock`，再构建 wheel。

## 四个入口

- `$stylefit-code`：按仓库约定或样例整理 Python 代码，保留接口并分别检查语法、静态接口和行为。
- `$stylefit-research`：依据提供的材料整理中英文科研文字，保留来源、单位、未知值和证据边界。
- `$stylefit-email`：按当前简报起草或改写中英文邮件，保留谁做什么、回复与执行期限、背景信息和承诺；只生成草稿。
- `$stylefit-profile`：仅在明确要求时建立或修改可选档案，不作为其他技能的前置问卷。

直接使用：`使用 $stylefit-code，按当前仓库约定简化这段代码，保留接口和行为，不建立档案。`

提供样例：`使用 $stylefit-email，参考这些确认样例的表达方式起草邮件；事实和行动只依据当前简报，不保存样例。`

已有 v1 档案继续可用，领域和语言相互隔离，未确定的习惯保持未知；公共默认设置不包含项目作者的偏好。更多流程见[示例](docs/EXAMPLES.md)。

## 实际检查后交付

流程为生成、执行检查、依据错误最多修订一次、再检查。必需检查失败或未运行时明确报告，不能用“看起来正确”冒充验证。任务规定的格式和字段优先；普通文字不强制包装成 JSON。

```sh
python3 path/to/stylefit-email/scripts/verify.py --artifact draft.json --schema schema.json --constraints constraints.json --report checks.json
```

检查器不修改成品。它会拒绝无效 JSON、字段错误以及明确事实契约中的数值、单位、空值或职责错误；日期只按声明的格式比较。正文与来源的对应关系另行复核，正确账本不等于正文正确。实际能力、返回码和验证缺口见[校验契约说明](docs/VERIFICATION.md)。

## 验收与发布

[英文说明](README.md)列出本地测试、构建及解压安装验收命令。CI 配置覆盖 Linux/macOS 和 Python 3.9/3.12，不自动调用收费模型；本机宿主验收、模型实验和远程 CI 的结果分别报告。

0.2 实验新增上限为 120 个 CLI 任务，在原有 239 个任务之上追加记账，失败、修订、评审和宿主测试均计入。全部显式指定 `gpt-6-luna / medium`，不回退其他型号；返回元数据未提供型号时如实记录。正式输入冻结，旧结果不覆盖。

原始记录、私人档案和盲评映射保存在忽略的 `.local/`。发布包按明确清单构建，附辅助 wheel 和 SHA-256；正式发布通道必须通过门槛且与已测产品哈希一致。不会自动公开到 GitHub。

不承诺作者识别、检测器结果、任意代码的完全行为等价或真实用户偏好。当前支持范围及局限以验收报告为准。
