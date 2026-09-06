# GlassMachine 文档（Documentation）

项目文档以中文为主。代码标识符、命令、格式字段、标准缩写和第三方工具名称保持原样，必要时在第一次出现处给出中英文对照。

## 阅读顺序（Reading Order）

1. [项目首页与路线图](../README.md)
2. [M0 完成与验收报告](milestones/m0-completion-report.md)
3. [M0 架构：可信仿真闭环](architecture/m0.md)
4. [数字逻辑规范 v1](specifications/digital-logic.md)
5. [ADR 0001：确定性事件内核](decisions/0001-deterministic-event-kernel.md)
6. [M0 验证报告](validation/m0.md)
7. [ADR 0002：固定传输延迟修正](decisions/0002-fixed-transport-delay.md)

## 文档职责（Documentation Responsibilities）

- `architecture/`：说明系统结构、职责边界和数据流。
- `specifications/`：定义可测试的输入、输出、状态和错误语义。
- `decisions/`：记录重要设计决策的背景、选择和后果。
- `validation/`：记录验证方法、覆盖对象和证据解释。
- `milestones/`：汇总里程碑目标、交付物、验收证据、结论与遗留边界。

工程代理长期遵守的产品与开发约束记录在仓库根目录的 [AGENTS.md](../AGENTS.md)。
