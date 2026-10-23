# OwnVoice Skills

面向所有使用者的四技能套件：代码、科研文字、邮件，以及可选风格档案。不提供档案也能直接使用；提供确认样例时，只参考表达习惯，事实和功能约束仍以任务为准。

**当前为 0.2.0 可发布候选，本轮模型与 Codex 宿主门槛已通过。** [验收报告](reports/release-v02.md) 记录实际结果；只有通过全部既定门槛才升级为正式版。此前[复杂诊断的负面结果](reports/luna-v2.md)和[通用适配结果](reports/general-v1.md)继续保留。

## 安装与维护

从包含辅助 wheel 的解压包中执行，需要 Python 3.9+：

```sh
python3 scripts/install.py --host codex --with-tools --dry-run
python3 scripts/install.py --host codex --with-tools
```

默认安装到 `~/.agents/skills`，也可用 `--dest` 指定项目目录。辅助工具运行在独立版本环境中，不改全局 Python、模型配置或认证，不覆盖用户已有的不同技能。

安装后在下一条消息中使用 `$ownvoice-code` 等入口；若自动发现未刷新，可重启 Codex。[当前用户目录实测记录](reports/user-install-v02.md)与原隔离宿主验收分开保存。

```sh
python3 scripts/install.py --host codex --with-tools --upgrade
python3 scripts/install.py --host codex --rollback
python3 scripts/install.py --host codex --uninstall
```

卸载只移除本工具管理的技能链接，保留缓存版本及用户档案。完整规则、离线依赖选项和 Claude 便携目录的验证边界见[安装说明](docs/INSTALLATION.md)。源码使用者先在选定虚拟环境安装 `requirements-dev.lock`，再构建 wheel。

## 四个入口

- `$ownvoice-code`：按仓库约定或样例整理 Python 代码，保留接口并分别检查语法、静态接口和行为。
- `$ownvoice-research`：依据提供的材料整理中英文科研文字，保留来源、单位、未知值和证据边界。
- `$ownvoice-email`：按当前简报起草或改写中英文邮件，保留谁做什么、回复与执行期限、背景信息和承诺；只生成草稿。
- `$ownvoice-profile`：仅在明确要求时建立或修改可选档案，不作为其他技能的前置问卷。

直接使用：`使用 $ownvoice-code，按当前仓库约定简化这段代码，保留接口和行为，不建立档案。`

提供样例：`使用 $ownvoice-email，参考这些确认样例的表达方式起草邮件；事实和行动只依据当前简报，不保存样例。`

已有 v1 档案继续可用，领域和语言相互隔离，未确定的习惯保持未知；公共默认设置不包含项目作者的偏好。更多流程见[示例](docs/EXAMPLES.md)。

## 实际检查后交付

流程为生成、执行检查、依据错误最多修订一次、再检查。必需检查失败或未运行时明确报告，不能用“看起来正确”冒充验证。任务规定的格式和字段优先；普通文字不强制包装成 JSON。

```sh
python3 path/to/ownvoice-email/scripts/verify.py --artifact draft.json --schema schema.json --constraints constraints.json --report checks.json
```

检查器不修改成品。它会拒绝无效 JSON、字段错误以及明确事实契约中的数值、单位、空值或职责错误；日期只按声明的格式比较。正文与来源的对应关系另行复核，正确账本不等于正文正确。实际能力、返回码和验证缺口见[校验契约说明](docs/VERIFICATION.md)。

## 验收与发布

[英文说明](README.md)列出本地测试、构建及解压安装验收命令。CI 配置覆盖 Linux/macOS 和 Python 3.9/3.12，不自动调用收费模型；本机宿主验收、模型实验和远程 CI 的结果分别报告。

0.2 实验新增上限为 120 个 CLI 任务，在原有 239 个任务之上追加记账，失败、修订、评审和宿主测试均计入。全部显式指定 `gpt-6-luna / medium`，不回退其他型号；返回元数据未提供型号时如实记录。正式输入冻结，旧结果不覆盖。

原始记录、私人档案和盲评映射保存在忽略的 `.local/`。发布包按明确清单构建，附辅助 wheel 和 SHA-256；正式发布通道必须通过门槛且与已测产品哈希一致。不会自动公开到 GitHub。

不承诺作者识别、检测器结果、任意代码的完全行为等价或真实用户偏好。当前支持范围及局限以验收报告为准。
