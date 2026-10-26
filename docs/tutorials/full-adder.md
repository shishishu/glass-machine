# 一位全加器实验（Full-adder Lab）

## 安装与入口（Installation and Entry Points）

在仓库根目录使用 Python 3.12 或更高版本：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev,gui]'
.venv/bin/glassmachine gui --model full-adder
```

不需要 GUI 时可仅安装 `.[dev]`。命令行入口：

```bash
.venv/bin/glassmachine full-adder --a 1 --b 1 --cin 0
.venv/bin/glassmachine verify --model full-adder
.venv/bin/glassmachine replay experiments/m1-full-adder.json
```

第一条的稳定结果为 Sum=0、Cout=1；第二条比较全部 64 组四态输入。原有 `not`、默认 `verify` 和默认 `gui` 仍使用 M0 NOT。

## 预测、观察与解释（Predict, Observe and Explain）

1. 先预测 A=0、B=1、Cin=1 的结果，再在界面选择这三个值。
2. 点击“输入入队”，此时输入按 A→B→Cin 排入，并未立即全部提交。状态栏显示待处理数量，传播中不进行稳定态比较。
3. 点击“单步”观察一次待处理项的提交，再点击“运行至稳定”。预期 Sum=0、Cout=1，三个模型一致。
4. 将 A 改为 1，保留 B=1、Cin=1，再次入队并单步。观察 p、g 先变化，Sum、h 随后变化；Cout 保持 1。
5. 运行至稳定后，预期 Sum=1、Cout=1。解释：三个 1 相加为二进制 11，其中低位为 Sum，高位为 Cout。

连线颜色表示源信号当前已提交的值：0 灰、1 绿、X 橙、Z 紫。文本也显示数值，不依赖颜色判断。交叉线不自动相连，同名信号属于同一网络。

“单步”处理一个队列项，可能只消费无变化输出；此时模型时间或待处理数改变，但不会伪造信号变化。事件列表中的 cause 是直接触发者 ID。tick 是模型时间，不是真实纳秒。

## 半加器、全加器与信号名（Half Adder, Full Adder and Signals）

半加器接收 A、B 两个一位数，输出 `Sum=A XOR B`、`Cout=A AND B`。它能产生进位，但没有输入进位端口。全加器增加 Cin，满足二态关系 `A+B+Cin = Sum+2×Cout`。

图中的整个五门网络是一个一位全加器，可以理解为两个半加器和一个 OR：第一个半加器产生 p（A/B 的本位和）与 g（进位）；第二个将 p 与 Cin 相加，产生 Sum 与 h；OR 合并 g/h 得到 Cout。最终二进制数按高位到低位写作 `Cout Sum`，窗口比较栏的 `Sum/Cout` 是字段顺序，不是二进制数的书写顺序。

## 日志阅读与可信度（Reading Events and Validation Results）

例如 `t=4 Δ=0 #21 Sum: X→1 cause=16`：

| 字段 | 含义 |
| --- | --- |
| t=4 | 模型时间 4 tick |
| Δ=0 | 这个时间点内的第 0 个传播轮次，不是门延迟，也不加到 t 上 |
| #21 | 事件编号；无变化待处理项不记录为变化事件，因此编号可能跳过 |
| Sum: X→1 | Sum 从未知变为 1 |
| cause=16 | 事件 #16 直接触发本次求值；不是时间，也不代表全部输入依赖 |
| cause=None | 没有父事件，例如外部输入 |

新事件安排到未来时刻时 Δ=0；安排在当前时刻时 Δ=当前 Δ+1。例如初始化结束于 t=2、Δ=0，立即输入排在 t=2、Δ=1；延迟 1 tick 的门响应在 t=3、Δ=0。若门延迟为 0，则响应在 t=2、Δ=2。相同 t/Δ 的多个输入仍按入队序号逐个执行，Δ 不会因为处理了一个事件就自动加一。

最后一条变化在 t=4，模型时间仍可能结束于 t=5：例如 h 的变化触发 OR 再次安排 Cout=1，t=5 提交时 Cout 已是 1，不新增日志，但时间已推进。这不表示有信号变化丢失。

稳定态 PASS 表示当前输入下三模型一致。结合已执行的全部 64 组四态穷举、二态整数对照及波形／GUI 回归，当前结果可以作为声明范围内可靠的学习依据；正常使用应持续 PASS，出现 FAIL 要排查。传播中不要求立即满足最终加法关系。PASS 不是对全部历史波形的实时证明，也不是物理时序校准，详见[验收报告](../milestones/m1-first-delivery-report.md)。

## 未知态实验（Unknown-value Experiment）

设置 A=1、B=X、Cin=1 并运行至稳定，预期 Sum=X、Cout=X，三模型仍应一致。将 X 改为 Z，门级求值仍把它视为未知。

为什么进位不是 1？本实验观察固定五门结构：p=X、g=X、h=X，OR 只能得到 X。虽然 B 的所有二态补全都有进位 1，但逐门四态运算丢失了相关性。这里的 X 表示抽象无法确定，不表示真实电路出现第三种稳定逻辑电平。详见[四态规格](../specifications/m1-combinational.md)。

## 保存与重放（Save and Replay）

GUI 运行至稳定后点击“保存实验”。“重置”后通过“加载并重放”验证并恢复实验；“导出轨迹”可保存当前已提交事件。保存未稳定实验会给出提示，继续运行后再保存即可。加载失败保留原电路。

命令行也可保存：

```bash
.venv/bin/glassmachine full-adder --a 1 --b 1 --cin 0 --record full-adder.json --trace full-adder.jsonl
.venv/bin/glassmachine replay full-adder.json
```

记录保存输入与单步／运行操作的顺序、完整期望轨迹及最终输出。重放重新计算并定位第一个事件分歧；它不只是播放已保存动画。

## Python 控制与验证（Python Control and Validation）

```python
from glassmachine.visualization.full_adder_controller import FullAdderController

controller = FullAdderController(delay=1)  # 无界面，不导入 Qt
for signal, value in (("A", "0"), ("B", "1"), ("Cin", "1")):
    controller.queue(signal, value)
controller.run()
controller.queue("A", "1")
controller.step()
controller.run()
print({name: str(value) for name, value in controller.simulation.signal_values().items()})
controller.save("full-adder.json")
```

更底层的组件实验使用 `build_full_adder_simulation()` 与 Simulation 的 `set_input()`、`step()`、`read()` 等公开接口。可运行 [Python 示例](../../examples/full_adder.py)。

```bash
.venv/bin/python examples/full_adder.py
.venv/bin/python -m pytest tests/test_m1_models.py tests/test_full_adder_validation.py tests/test_full_adder_timing.py tests/test_full_adder_experience.py -q
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_full_adder_gui.py -q
```

练习：先预测 1+0+0、1+0+1 的结果，再尝试同刻交换 A/B。比较稳定答案和中间事件是否相同。它们可以有相同答案、不同传播路径；三模型功能比较与波形验证解决的是不同问题。
