# M0 完成与验收报告（M0 Completion and Acceptance Report）

## 文档信息（Document Information）

| 项目 | 内容 |
| --- | --- |
| 里程碑 | M0 — 可审计仿真基础 |
| 状态 | 已验收 |
| 验收日期 | 2026-08-30 |
| 功能实现基线 | `13ad5ca` — `feat: complete M0 simulation foundation` |
| CI 修正基线 | `00166af` — `ci: install Qt runtime for GUI smoke test` |
| 许可证 | MIT |

本文是 M0 的集中归档。它汇总目标、设计、交付物、验证证据、结论强度、遗留边界和进入 M1 的条件。详细定义仍分别由架构、规格、ADR 和验证文档承担。

## 1. 目标与动机（Goals and Motivation）

M0 的目的不是先制造大量逻辑门，而是建立一个可信的最小闭环，回答后续每个模块都会遇到的问题：

- 谁拥有真实状态？
- 同一时刻的传播顺序如何确定？
- 可视化显示的是仿真事实还是预制动画？
- 如何单步、观察、保存和重新计算一次运行？
- Python 实现如何避免同时充当没有独立依据的“运动员和裁判员”？
- 后续加法器、寄存器、CPU、Memory 和 Attention 如何复用同一基础设施？

因此，M0 选择四态 NOT 作为最小基础设施验证切片，用最简单的逻辑功能检验完整的仿真、追踪、调试、验证和可视化链路。M1 的一位全加器才是第一个面向体系结构学习的完整垂直切片。

## 2. M0 范围（M0 Scope）

### 包含

- `0/1/X/Z` 四态逻辑与显式位宽；
- 组件、端口、信号与单驱动契约；
- 确定性离散事件内核；
- 模型时间、delta cycle 和声明延迟；
- 类型化事件、因果关系和版本化 JSONL 轨迹；
- 稳定态快照、恢复、事件单步、探针和断点；
- 可序列化实验与通过重新计算完成的重放；
- NOT 的 Reference／Detailed／Fast 三模型；
- CLI、Python 示例和最小 PySide6 可视化；
- 自动测试、静态检查、覆盖率门槛和 CI。

### 不包含

- 连续电压、晶体管器件模型和 SPICE；
- NAND、AND、OR、XOR、半加器、全加器和多位加法器；
- 时钟、锁存器、触发器和寄存器；
- 多驱动总线解析；
- ALU、ISA、CPU 和完整计算机；
- Cache、DRAM、SSD、互联和 Attention；
- 与真实硬件校准的时间、功耗或面积。

## 3. 核心设计（Core Design）

### 3.1 事实流

```text
用户操作 / Python 实验
          ↓
仿真器提交真实状态变化
          ↓
产生统一状态与类型化事件轨迹
       ↙                    ↘
可视化 / 调试              自动验证 / 重放
```

可视化不修改信号，测试也不绕过仿真器直接制造“看起来正确”的结果。详细结构见 [M0 架构](../architecture/m0.md)。

### 3.2 状态与时间

`Simulation` 是已提交信号状态的唯一所有者。组件读取不可变输入并返回拟议输出。所有事件按 `(time, delta, sequence)` 排序，从而使相同配置和输入产生相同执行顺序。

`time` 只是整数模型时间；M0 只验证声明的相对延迟，不把它解释为真实纳秒。

### 3.3 四态逻辑

`X` 显式表示未知，`Z` 显式表示未驱动／高阻。NOT 的规范为 `0→1`、`1→0`、`X→X`、`Z→X`。完整语义和错误规则见 [数字逻辑规范 v1](../specifications/digital-logic.md)。

### 3.4 三模型验证

- `ReferenceNot`：不可变真值表，强调规格可读性；
- `NotGate`：参与事件传播的详细组件；
- `FastNot`：独立字符转换实现，为未来大规模组合预演 fast path。

三套实现接口一致，但没有共享同一个 NOT 求值函数。测试再以真值表字面量作为外层断言，降低同源错误导致“自己证明自己”的风险。

### 3.5 可审计与可重放

每次真实提交的值变化生成不可变 `TraceEvent`。实验记录保存输入配置、期望输出和轨迹摘要；重放重新构造并执行电路，而不是播放已保存事件。

## 4. 交付物（Deliverables）

| 能力 | 主要位置 | 状态 |
| --- | --- | --- |
| 四态逻辑与位宽 | `src/glassmachine/core/logic.py` | 完成 |
| 组件与端口契约 | `src/glassmachine/core/component.py` | 完成 |
| 离散事件内核 | `src/glassmachine/simulation/engine.py` | 完成 |
| 事件与轨迹 | `src/glassmachine/trace/` | 完成 |
| 调试器 | `src/glassmachine/debugging/debugger.py` | 完成 |
| NOT 三模型 | `src/glassmachine/models/{reference,digital,fast}/` | 完成 |
| 可复现实验 | `src/glassmachine/experiments/not_gate.py` | 完成 |
| 固定实验记录 | `experiments/m0-not.json` | 完成 |
| 差分验证 | `src/glassmachine/validation/not_gate.py` | 完成 |
| Python 示例 | `examples/not_gate.py` | 完成 |
| CLI | `src/glassmachine/cli.py` | 完成 |
| PySide6 可视化 | `src/glassmachine/visualization/` | 完成最小范围 |
| 测试与 CI | `tests/`、`.github/workflows/ci.yml` | 完成 |
| 架构、规格、ADR、验证文档 | `docs/` | 完成 |

## 5. 验收方法与结果（Acceptance Methods and Results）

验收命令和各类证据的详细解释见 [M0 验证报告](../validation/m0.md)。记录结果如下：

| 验收项 | 结果 | 说明 |
| --- | --- | --- |
| pytest | 通过 | 25 项测试全部通过 |
| 语句覆盖率 | 通过 | 79.01%，门槛为 75% |
| Ruff | 通过 | 无 lint 错误 |
| mypy strict | 通过 | 27 个源文件无类型错误 |
| NOT 穷举 | 通过 | `0/1/X/Z` 的三模型结果一致 |
| 确定性 | 通过 | 独立运行产生相同轨迹摘要 |
| 重放 | 通过 | 重新计算后的输出与摘要匹配 |
| GUI controller | 通过 | 状态来自同一仿真内核 |
| GUI smoke | 通过 | PySide6 offscreen 启动并退出 |
| GitHub Actions | 通过 | Python 3.12、3.13 与 GUI smoke 全部通过 |

通过的 CI 运行：[CI run 33312743654](https://github.com/shishishu/glass-machine/actions/runs/33312743654)。

固定实验重算的最终输出为 `X`，轨迹 SHA256 摘要为 `8fb957f87b446a02f31f230df847f6062d8ea8d2eaecb7fef19fa21b0ed7f1fc`。

覆盖率只表示测试运行经过的语句比例，不是正确率。M0 的可靠性来自规格、独立模型、穷举比较、不变量、重算式重放和 CI 等多种证据的组合。

## 6. 完成标准对照（Definition of Done Mapping）

| 完成标准 | M0 证据 | 结论 |
| --- | --- | --- |
| 书面规格与公开契约 | 数字逻辑规范、组件／端口类型 | 满足 |
| 假设与抽象损失 | 架构和本报告的范围边界 | 满足 |
| Ground truth | NOT 四态真值表 | 满足 |
| 独立参考实现 | Reference／Detailed／Fast 三条路径 | 满足 |
| 正常、边界、非法测试 | 25 项自动测试 | 满足 M0 范围 |
| 确定性轨迹 | 全序事件、稳定摘要、因果字段 | 满足 |
| 差分验证 | 四态输入穷举比较 | 满足 |
| 无界面可复现实验 | CLI、Python 示例、实验记录 | 满足 |
| 同源可视化 | GUI controller 读取真实仿真状态 | 满足最小范围 |
| 来源与许可证 | MIT；M0 核心未引入复制实现 | 满足 |

## 7. 已证明的结论（Established Conclusions）

在 M0 明确限定的范围内，可以接受以下结论：

1. GlassMachine 已具备可复用的确定性组合逻辑事件内核。
2. NOT 的功能结果有明确规格，并通过三模型和穷举测试验证。
3. 状态变化可以被追踪、保存、检查因果并通过重新计算重放。
4. Python API、CLI、调试器、实验、验证和 GUI controller 已围绕同一仿真事实来源形成闭环。
5. 当前基础足以承载 M1 的门、加法器和寄存器，而不需要重写 M0 核心数据模型。

## 8. 尚未证明的结论（Conclusions Not Established）

M0 不证明：

1. 任何晶体管节点的真实电压或随时间变化的模拟波形；
2. 模型 tick 与真实秒、纳秒或具体芯片频率的对应关系；
3. 时序逻辑、多驱动总线或完整 CPU 的正确性；
4. GUI 的所有交互都经过完整自动化测试；
5. 当前性能足以运行大规模 CPU、Memory 或 LLM 工作负载；
6. 语句覆盖率能够替代功能规格和独立 ground truth。

## 9. 已知限制与技术债（Known Limitations and Technical Debt）

- GUI 窗口本身目前只有启动 smoke test；交互逻辑主要通过无界面 controller 测试。
- JSONL 已版本化，但尚未经历真实格式迁移；首次破坏性变更前需要明确兼容策略。
- 单驱动规则是有意的 M0 限制，不能被误解为已经支持三态总线。
- 事件预算能够发现无法稳定，但目前不提供完整环路诊断图。
- trace 为完整事件流；进入更大模型前，需要设计可配置过滤和采样，同时不能破坏审计语义。
- 当前延迟是抽象 tick；物理解释必须等待外部模型或真实系统校准。

## 10. M1 准入条件（M1 Entry Criteria）

M1 可以在不修改 M0 已验收结论的前提下开始，并应满足：

- 基础门和一位全加器继续提供规格、Reference／Detailed／Fast 模型与穷举验证；
- 参数化 4／8 位加法器以整数数学作为独立 ground truth；
- 引入明确的时钟边沿、setup／commit 和寄存器状态转移语义；
- 选择少量 CMOS 局部电路，通过 ngspice 做第三方交叉验证；
- 可视化仍只消费仿真状态和真实轨迹；
- 新能力不得把 M0 的抽象 tick 冒充真实硬件时间。

## 11. 最终验收结论（Final Acceptance Conclusion）

**M0 通过验收。**

该结论仅表示“可审计仿真基础”达到既定范围：已有确定性事件内核、四态逻辑、三模型 NOT、轨迹、调试、重算式重放、最小可视化和自动验证闭环。它不表示晶体管、加法器、寄存器或 CPU 已经完成。

M0 可以冻结为后续里程碑的可信基础；若未来修改其公开语义、轨迹格式或确定性规则，必须更新相关规格、ADR、回归测试和本报告所引用的结论。
