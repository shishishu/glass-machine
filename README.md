# GlassMachine

> **From Bit to Attention**

**GLASS** = **G**rounded, **L**ayered, **A**uditable **S**ystems **S**imulator  
有依据、分层、可审计的计算系统模拟器。

- 完整品牌：**GlassMachine**
- 简称：**GLASS**
- 仓库名：`glass-machine`
- Python 包名：`glassmachine`
- 当前状态：M0 可信仿真闭环完成（pre-alpha）

## 快速开始

核心包没有运行时第三方依赖：

```bash
python -m pip install -e .
glassmachine verify
glassmachine not --inputs 0,1,X,Z
glassmachine replay experiments/m0-not.json
```

开发与可选 GUI：

```bash
python -m pip install -e ".[dev,gui]"
pytest
glassmachine gui
```

如果尚未安装 package，也可以直接运行：

```bash
PYTHONPATH=src python -m glassmachine verify
```

## 文档导航

项目文档以中文为主；代码标识符、命令、格式字段和通用技术缩写保持原样。

- [文档首页](docs/README.md)
- [M0 完成与验收报告](docs/milestones/m0-completion-report.md)
- [M0 架构：可信仿真闭环](docs/architecture/m0.md)
- [数字逻辑规范 v1](docs/specifications/digital-logic.md)
- [ADR 0001：确定性事件内核](docs/decisions/0001-deterministic-event-kernel.md)
- [M0 验证报告](docs/validation/m0.md)

## 愿景

GlassMachine 是一个 Python-first 的可执行计算系统实验室。项目从晶体管、逻辑门、加法器和寄存器出发，逐步构造 ALU、CPU 与完整的小型计算机，再继续展开 Cache、DRAM、虚拟内存、SSD、并行计算、通信互联、矩阵加速器与 Attention。

项目始终围绕一个问题展开：

> 数据从哪里来，现在在哪里，为什么移动，正在等待什么，在哪里计算，以及改变系统结构后会发生什么？

GLASS 不以复刻某款商业处理器为目标，也不以堆砌尽可能多的晶体管为目标。我们追求的是**行为真实、因果可见、结果可验证、实验可复现**。

## 核心目标

1. **Grounded — 有依据**  
   每个重要结果都应有数学定义、参考模型、外部工具或真实测量作为 ground truth；不能以“动画看起来合理”代替正确性。

2. **Layered — 分层**  
   同一个系统可以在晶体管、逻辑门、RTL、微体系结构、Memory、互联和张量等尺度间展开或折叠。

3. **Auditable — 可审计**  
   每次状态变化都产生可追踪、可保存、可重放的事件；用户可以回答“谁在何时、因为什么改变了这个值”。

4. **Programmable — 可编程**  
   GUI 与 Python API 使用同一个仿真内核。用户可以修改输入、程序、Memory 参数、互联结构和计算单元，而不是只能观看固定课件。

5. **Progressively complete — 逐步完备**  
   前一阶段验证过的组件成为后一阶段的真实基础。系统从局部生长成整体，旧模型同时保留为入门模式和正确性基准。

## 项目要达到的体验

用户应当能够：

- 运行、暂停、单步、回退和重放；
- 修改输入、寄存器、内存、程序和体系结构参数；
- 设置指令、周期、信号、地址、事务和协议状态断点；
- 给线路、Cache line、packet 和 tensor tile 添加探针；
- 从整机钻取到 ALU、加法器、逻辑门或局部晶体管；
- 观察同一工作负载在不同体系结构中的数据路径；
- 比较结果、周期、数据移动量、命中率、带宽和利用率；
- 导出可以独立复现的实验配置、结果和执行轨迹。

可视化永远不是事实来源。正确的数据流是：

```text
用户操作 / Python 实验
          ↓
仿真器执行真实状态变化
          ↓
生成统一状态与事件轨迹
       ↙          ↘
可视化与调试       自动验证
```

## 多模型架构

关键组件可以拥有三个相互独立、接口一致的模型：

- **ReferenceModel**：最简单、最容易判断正确性的参考实现；
- **DetailedModel**：晶体管、门级、RTL 或周期级实现，用于深入观察；
- **FastModel**：用于把组件组合进更大系统的快速行为模型。

它们对相同输入进行差分验证。整机可以使用快速模型运行；当用户钻取某次操作时，系统使用该操作的真实边界输入在详细模型中重放，并再次与参考结果比较。

## 技术方向

GlassMachine 以 Python 为主要实现与扩展语言：

- Python：仿真内核、参考模型、实验、调试、验证与用户 API；
- PySide6：桌面可视化；
- pytest / Hypothesis：穷举、属性和回归测试；
- SPICE/ngspice：少量晶体管级局部验证；
- PyRTL / Verilog / Icarus Verilog：数字硬件与 RTL 交叉验证；
- NumPy / PyTorch：矩阵、Attention 与 LLM 数值 ground truth。

RTL 会参与加法器、寄存器、ALU、CPU 数据通路、控制器、Cache controller、互联 router 和加速器局部，但不会强迫整个系统都采用 RTL。Memory 系统、通信互联和大型工作负载更适合 Python 离散事件模型。

## 发展路线

### M0 — 可审计仿真基础

- [x] 四态逻辑、显式位宽、组件、端口和信号契约；
- [x] 确定性 `(time, delta, sequence)` 事件调度；
- [x] 稳定态快照、事件级调试和重放；
- [x] Reference/Detailed/Fast 模型契约与 NOT 三模型；
- [x] 无界面 CLI 与可选 PySide6 最小可视化；
- [x] 版本化 JSONL 轨迹、差分验证、测试和 CI。

### M1 — 从晶体管到寄存器

- CMOS 基本门；
- 半加器、全加器和 4/8 位加法器；
- 触发器、时钟、写使能和寄存器；
- 数学、门级、RTL 与局部 SPICE 结果对照。

第一个垂直切片是一位全加器：允许自由输入、单步观察、保存轨迹，并自动比较参考、详细与快速模型。

### M2 — 完整的 8 位小型计算机

- 运算器、控制器、存储器、输入和输出；
- 8 位 ALU、寄存器、PC、IR、FLAGS 与总线；
- 自定义小型 ISA、汇编器、反汇编器与独立解释器；
- 可运行循环、分支、内存复制和输入输出程序。

8 位 CPU 是完整的标量计算机、后续加速器的控制核心，也是所有优化版本的正确性基线；它不是项目永久的算力上限。数据宽度、地址宽度、传输宽度和累加宽度不得在底层接口中绑定。

### M3 — 存储层级（Memory hierarchy）

- 理想内存、DRAM、L1 与多级 Cache；
- Tag/Index/Offset、替换、写回与延迟；
- TLB、虚拟内存、Page fault 与 SSD 页面调入；
- 相同程序在不同 Memory 配置下的结果与数据移动对比。

### M4 — 并行与通信互联

- 多核、私有与共享 Cache；
- Cache coherence 与 false sharing；
- Bus、Crossbar、Ring、Mesh；
- 队列、带宽、延迟、拥塞、背压、NUMA 与 DMA。

### M5 — 矩阵计算与注意力机制（Attention）

- MAC、SIMD、PE Array / Systolic Array；
- SRAM tile buffer、分块矩阵乘法与数据复用；
- 真实 Q/K/V、Mask、Softmax 与 KV Cache；
- Naive、Tiled 与 IO-aware Attention 的数值和数据移动对比。

### M6 — 微型 Transformer／LLM

- 固定小型 tokenizer 与真实权重；
- Prefill、自回归 Decode 与 KV Cache；
- 参考框架 logits 对照；
- 整体采用张量级快速执行，选中局部可钻取到周期、RTL、门或晶体管。

## 验证策略

GLASS 使用多层 ground truth：

| 层级 | 验证依据 |
| --- | --- |
| 晶体管 | SPICE 瞬态仿真与明确器件模型 |
| 逻辑门 | 布尔代数与穷举真值表 |
| 加法器 / ALU | 整数数学、边界条件与标志位规则 |
| 寄存器 | 状态转移表与时钟语义 |
| CPU | 独立 ISA 解释器、逐指令状态比较与 RTL 仿真 |
| Cache / Memory | 独立参考模型、访问轨迹与协议不变量 |
| 多核 | 一致性不变量与 litmus tests |
| Attention | NumPy/PyTorch、明确精度与数值容差 |
| 微型 LLM | 固定权重、固定输入、固定随机种子与参考 logits |

每个核心模块在完成前必须具备：规格、参考模型、详细或结构模型、测试、轨迹、可视化、边界说明和验证记录。

## 项目边界

GLASS 明确不以以下内容为近期目标：

- 完整晶体管级 CPU 或商业芯片版图；
- 逐电子物理模拟；
- 精确复刻 x86、现代 RISC-V CPU 或商业 GPU；
- 以 3D 漫游和物理堆砌为主要交互；
- 过早实现乱序执行、复杂流水线和完整操作系统；
- 用门级模型运行大型 LLM；
- 未经真实硬件校准就声称周期或性能等同现实设备。

晶体管层用于理解和验证重要局部，而不是承载整个系统。GLASS 追求的是**语义真实高于几何写实**。

## 重造轮子的原则

我们接受为了理解而重新实现已有机制，但不以“所有代码原创”为目标：

> 重造我们想理解、观察和实验的机制；复用与核心认知无关的基础设施。

参考已有项目时，应记录：学习了什么、采用了什么、为什么与原项目不同、保留和舍弃了哪些语义、ground truth 是什么。直接引用代码时必须遵守许可证并保留来源。

## 当前阶段

M0 已建立输入、仿真、事件、调试、可视化、验证与重放的可信闭环，并形成了 [M0 完成与验收报告](docs/milestones/m0-completion-report.md)。下一阶段进入 M1：加入基础门、全加器、参数化多位加法器和寄存器，并为选中的晶体管局部接入 SPICE 第三方验证。
