# OwnVoice 0.2.0 远程 CI 验收

2026-10-23。在私有 GitHub 验证仓库实际执行，[工作流 39924987495](https://github.com/Fanmili-5/ownvoice-skills/actions/runs/39924987495) 全部成功。对应提交为 `97aebf80990eb40404c084e60e823956a3c64d3a`。

| 系统 | Python | 结果 |
| --- | --- | --- |
| Linux / ubuntu-latest | 3.9 | success |
| Linux / ubuntu-latest | 3.12 | success |
| macOS / macos-latest | 3.9 | success |
| macOS / macos-latest | 3.12 | success |

每组实际完成：锁定依赖安装、54 项测试、四技能静态校验、发布白名单审计、wheel 构建、128 文件候选包构建，以及解压后的安装验收。分发验收还运行解压源码测试，创建实际隔离环境，检查安装后工具正反例，并执行合成维护版本的升级、回滚、恢复调用和卸载，共 11 项记录。

维护版本复用同一 helper 产品负载，证明安装事务与环境可用，不替代不同 helper 版本的兼容性验证。本机此前 rc1→0.2.0 的运行环境升级及回滚单独保留。

这是首个冻结软件候选的执行回执。之后添加本回执等文档与摘要，不改变技能或 helper；最终分支仍重新执行同一四组工作流，最终发布说明引用该确切提交和运行。此回执不以修改自身来冒充尚未完成的后续运行。

全部 CI 不调用模型。它不证明模型风格优势、作者检测结果、Claude 调用或独立人类偏好。原始 CI 日志留在本地及 GitHub Actions，公开摘要见 [JSON](ci-v02.json)。
