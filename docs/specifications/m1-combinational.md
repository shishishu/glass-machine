# M1 首次交付规格：基础门与一位全加器（M1 Combinational Slice Specification）

## 范围与事实来源（Scope and Source of Truth）

本规格覆盖 M1 第一次交付 A+B+C：二输入 AND／OR／XOR、半加器、一位全加器及实验体验。沿用 [M0 数字逻辑](digital-logic.md) 的单驱动、显式位宽和固定传输延迟。四态与电路结构的选择见 [ADR 0003](../decisions/0003-full-adder-four-state-semantics.md)。

数学与本文的真值表是功能依据；Detailed 是主执行路径，UI 只消费仿真状态与事件。模型时间是 tick，没有物理时间校准。多位加法器、寄存器、时钟、RTL／SPICE 属于后续交付。

## 基础门的四态规则（Four-state Gate Semantics）

输入 `Z` 保留为信号状态，求值时按 `X` 处理。下面每格为 `AND / OR / XOR` 输出：

| A \ B | 0 | 1 | X | Z |
| --- | --- | --- | --- | --- |
| 0 | 0/0/0 | 0/1/1 | 0/X/X | 0/X/X |
| 1 | 0/1/1 | 1/1/0 | X/1/X | X/1/X |
| X | 0/X/X | X/1/X | X/X/X | X/X/X |
| Z | 0/X/X | X/1/X | X/X/X | X/X/X |

AND 的 0 和 OR 的 1 为控制值；XOR 只在两个输入均已知时给出已知值。输出不主动产生 Z。各输入、输出均为一位 `LogicVector`，宽度不匹配明确失败。

## 半加器与全加器结构（Adder Structure）

半加器：`Sum = XOR(A,B)`，`Cout = AND(A,B)`。

一位全加器固定采用以下五门结构：

```text
p    = XOR(A, B)
g    = AND(A, B)
Sum  = XOR(p, Cin)
h    = AND(p, Cin)
Cout = OR(g, h)
```

信号名称为 `A,B,Cin,p,g,h,Sum,Cout`，其中前三个为外部输入。初始化均为 Z，初始化传播后内部／输出成为相应的已知值或 X。构造器初始化并运行至稳定，实验时间以该稳定时刻为原点。每个门使用同一个显式非负整数延迟参数，默认 1 tick。

二态预期为 `total=A+B+Cin`、`Sum=total%2`、`Cout=total//2`。八个输入组合全部穷举。

含未知输入时，采用上面门结构的四态结果，不采用对所有二态补全求最精确值的算术模型。以下表格按列 Cin=0、1、X 列出 `(Sum,Cout)`；Z 归一为 X，共覆盖 64 组原始四态输入：

| A,B | Cin=0 | Cin=1 | Cin=X |
| --- | --- | --- | --- |
| 0,0 | 0,0 | 1,0 | X,0 |
| 0,1 | 1,0 | 0,1 | X,X |
| 0,X | X,0 | X,X | X,X |
| 1,0 | 1,0 | 0,1 | X,X |
| 1,1 | 0,1 | 1,1 | X,1 |
| 1,X | X,X | X,X | X,X |
| X,0 | X,0 | X,X | X,X |
| X,1 | X,X | X,X | X,X |
| X,X | X,X | X,X | X,X |

例如 `A=1,B=X,Cin=1` 得到 `Sum=X,Cout=X`。这表示结构丢失了输入相关性，不表示某个真实稳定的二态补全会产生进位 0。

## 模型接口与独立性（Model Interfaces and Independence）

- 公共结果 `AdderResult(sum: LogicVector, carry: LogicVector)`，其中 carry 对应电路信号 Cout。
- `ReferenceFullAdder.evaluate(a,b,cin)` 与 `FastFullAdder.evaluate(a,b,cin)` 接收一位 LogicVector，返回 AdderResult；半加器接收 a,b。
- `build_full_adder_simulation(delay=1)`／`build_half_adder_simulation(delay=1)` 返回已初始化稳定的 Simulation；通过其公开 API 设置输入、推进和读取状态。
- Reference 使用二态整数算术和显式四态结果表；Detailed 由基础门逐个求值与调度；Fast 使用独立直接逻辑实现。不得共同调用一个加法器求值函数来互相证明。
- 比较仅在队列为空时解释为稳定功能比较。传播期间显示当前状态与待处理数量，不把暂态误报为功能失败。

## 传播与输入顺序（Propagation and Input Ordering）

输入操作逐个提交，不是原子三元组更新。每次门求值的拟议输出都入队，仅提交时去掉无变化项。零延迟沿 delta 推进，同键按 sequence 排序。caused_by 表示直接触发求值的事件，不是所有操作数来源的集合。

标准波形例：所有门延迟 1，先稳定在 A=0、B=1、Cin=1，于 t 改 A=1，则 t+1 时 p:1→0、g:0→1，t+2 时 Sum:0→1、h:1→0，Cout 无变化事件。时间例需以已稳定的初始输入为前提。

短脉冲、同刻多输入和不同路径可产生暂态，完整轨迹是验证对象。不得根据最终答案反推中间波形正确。

## 实验、调试与重放（Experiments, Debugging and Replay）

实验需保留输入与推进操作的顺序，因为交互式单步与预先批量安排输入会改变事件序号。记录使用独立的 full-adder kind 与版本；不改变已有 NOT 记录。

记录包含配置、操作序列、期望输出及完整期望轨迹；重放重新创建仿真并执行操作，比较轨迹并报告首个分歧。完整实验保存要求运行稳定；传播中的状态可以继续单步或运行，轨迹可单独导出。重放一致性不代替真值表和波形依据。

界面至少提供三路四态输入、排入输入、事件单步、运行至稳定、重置、内部连线／信号、事件列表、稳定后三模型比较，以及保存／读取实验和导出轨迹。视图不得修改体系结构状态。

## 验证边界（Validation Boundaries）

验证覆盖每个基础门的 16 组输入、半加器的 16 组输入、全加器的 64 组输入；二态另对照整数算术。使用独立手工波形与因果预期验证传输延迟，保留全部 M0 回归。非法位宽、输入、延迟、记录格式与篡改重放需明确失败。

GUI 启动、程序化交互与人工／Agent 体验分别报告。三模型一致不证明物理真实性；独立 Agent 检查也不证明真实用户学习效果。
