# GlassMachine 文档（Documentation）

项目文档以中文为主。代码标识符、命令、格式字段、标准缩写和第三方工具名称保持原样，必要时在第一次出现处给出中英文对照。

## 阅读顺序（Reading Order）

1. [项目首页与路线图](../README.md)
2. [项目定位、AI PM 目标与 Agent 协作](project-positioning.md)
3. [M0 完成与验收报告](milestones/m0-completion-report.md)
4. [M0 架构：可信仿真闭环](architecture/m0.md)
5. [数字逻辑规范 v1](specifications/digital-logic.md)
6. [ADR 0001：确定性事件内核](decisions/0001-deterministic-event-kernel.md)
7. [M0 验证报告](validation/m0.md)
8. [ADR 0002：固定传输延迟修正](decisions/0002-fixed-transport-delay.md)
9. [M1 开发计划：从逻辑门到寄存器](milestones/m1-development-plan.md)

## 文档职责（Documentation Responsibilities）

- `project-positioning.md`：记录兴趣驱动的项目定位、职业目标、Agent 推进与评估方法及证据边界。
- `architecture/`：说明系统结构、职责边界和数据流。
- `specifications/`：定义可测试的输入、输出、状态和错误语义。
- `decisions/`：记录重要设计决策的背景、选择和后果。
- `validation/`：记录验证方法、覆盖对象和证据解释。
- `milestones/`：记录里程碑开发计划，并汇总交付物、验收证据、结论与遗留边界；计划不代表已交付。

工程代理长期遵守的产品与开发约束记录在仓库根目录的 [AGENTS.md](../AGENTS.md)。
