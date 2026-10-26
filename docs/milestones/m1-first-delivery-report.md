# M1 第一次交付报告：一位全加器（M1 First Delivery Report）

## 范围与状态（Scope and Status）

- 日期：2026-10-26。
- 基础提交：`78fe495`；本文随 M1 首次交付一同归档，具体交付提交可通过本文件的 Git 历史定位。
- 范围：计划中的 A 基础门、B 半加器／一位全加器、C 首次实验与可视化。
- 状态：首次交付本地验收完成。D 多位加法器、E/F 时序与寄存器、G RTL／SPICE 尚未交付。

使用入口见[全加器实验](../tutorials/full-adder.md)，公开契约见[首次交付规格](../specifications/m1-combinational.md)。

## 交付内容（Deliverables）

| 内容 | 代码／产物 |
| --- | --- |
| 三种基础门和半加器／全加器三模型 | `models/digital/{reference,detailed,fast}/{gates,full_adder}.py` |
| 类型化结果 | `models/digital/adder.py` 的 AdderResult |
| 四态穷举与差分报告 | `validation/full_adder.py` |
| 可重放操作序列及完整期望轨迹 | `experiments/full_adder.py`；固定记录 `experiments/m1-full-adder.json` |
| 无界面控制器与真实五门图 | `visualization/full_adder_controller.py`、`full_adder_demo.py` |
| CLI 与 Python 示例 | `full-adder`、`verify/gui --model full-adder`、`examples/full_adder.py` |
| 规格、决策和教程 | 四态规格、ADR 0003、全加器实验教程 |

未修改 M0 仿真内核或旧实验格式。默认 NOT 命令保持兼容。界面提供输入入队、单步、运行、重置、保存、加载并重放和导出轨迹；传播中不误报稳定态比较结果。

## 关键决策与协作证据（Decisions and Collaboration Evidence）

先明确四态与接口，再按模型实现、实验体验和独立验证分工，主 Agent 集成并审查。后续独立 Agent 仅依据公开文档执行任务，没有阅读源码。该过程是工具操作证据，不是学习效果研究。

重要决策与纠偏：

- 全加器四态采用固定五门结构的保守结果，避免把理想算术补全与门级抽象的差异误判为缺陷，见 [ADR 0003](../decisions/0003-full-adder-four-state-semantics.md)。
- 记录保存输入与推进动作交错顺序，而不是只保存输入时间，确保交互重放的事件序号和因果一致。
- 独立评审发现浮点／布尔延迟被基础契约放行；在 M1 门边界补充严格整数检查与回归，未扩改 M0。
- 集成时遇到一次 Qt 退出崩溃。明确 scene 所有权、移除按钮回调对窗口的强引用循环，并在 QApplication 存活期间销毁窗口树；新增三个独立进程退出回归。无法将偶发问题唯一归因于某个具体对象，因此只报告观察到的问题、修正与复测结果。
- 公开入口体验发现全加器入口较深、Python 原始对象输出不够直观；README 增加直接入口，教程将信号值转成字符串展示。
- 新 GUI 的类型检查依赖可选 PySide6；核心 CI 不安装它，因此将窗口代码的显式类型检查放到 GUI 任务，核心控制器仍保留 strict 检查。另建仅安装 dev 的虚拟环境确认核心测试和类型检查可独立运行。
- 实际体验讨论暴露出半加器／全加器、Sum/Cout 顺序、日志 t/Δ/cause 和 PASS 含义的解释缺口；将具体示例补入教程，不把全部解释堆到运行界面。
- 提交前独立代码审查未发现阻断问题；清理未被任何调用方使用的 `output_of()` 包装函数，避免无实际用途的公开接口。

## 本地验证结果（Local Validation Results）

环境：macOS、Python 3.12.8、PySide6 6.12.0，Qt offscreen。

| 检查 | 实际结果与范围 |
| --- | --- |
| 完整 pytest | 133 项通过，包含 M0 回归、M1 模型／时序／实验／GUI；其中生命周期测试运行 3 个独立 GUI 进程 |
| 覆盖率 | 85.04%，达到原 75% 门槛；不是正确率或完整证明 |
| 仅安装 dev 的独立环境 | 128 项通过、2 项 GUI 检查跳过，覆盖率 75.24%；核心 mypy 通过，GUI 在独立任务检查 |
| Ruff | 全仓检查通过 |
| mypy strict | 核心 38 个源文件通过；新 GUI 文件在有 PySide6 的环境单独通过；核心 `--no-site-packages` 检查通过 |
| 全加器三模型 | 64 组四态结果一致，二态另对照整数和，基础门与半加器也有穷举 |
| 时序 | 独立手工波形：短脉冲、同刻输入次序、重汇合暂态、零延迟 delta、进位路径与因果 |
| 重放 | 原 M0 两份实验及新增固定 M1 实验通过；交互保存／加载／继续运行及损坏记录回归通过 |
| GUI | 实际 Qt 按钮、文件对话框路径（测试中选择临时路径）、图中状态、延迟显示及退出验证通过；已查看本地截图 |
| 公开入口 Agent | CLI 1+1+0、64 组 verify、固定 replay、Python 示例和 1/X/1 均成功；控制器示例保存后 CLI 重放成功 |

固定 M1 实验先输入 0/1/1，稳定后改变 A=1，包含单步操作，最终 Sum=1、Cout=1。轨迹摘要为 `cbf3e54c79248a2ab09a2a916c357266c91ccbfccca27b0e105d215c56c4510c`。摘要用于回归；正确性依据另由真值表与完整波形给出。

复验命令（仓库根目录）：

```bash
.venv/bin/ruff check .
.venv/bin/mypy
.venv/bin/mypy src/glassmachine/visualization/full_adder_demo.py
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest --cov=glassmachine --cov-report=term-missing --cov-fail-under=75
.venv/bin/glassmachine verify --model full-adder
.venv/bin/glassmachine replay experiments/m1-full-adder.json
QT_QPA_PLATFORM=offscreen .venv/bin/glassmachine gui --model full-adder --smoke
```

## 边界与下一步（Limits and Next Steps）

CI 配置已增加全加器验证、固定重放、GUI 类型检查及交互／退出测试。本报告记录本地验收，不代表远端 CI 已通过；远端状态应查看对应交付提交的 Actions 结果。没有在本轮本地运行 Python 3.13 或 Linux；没有真实用户学习效果证据。

当前 Detailed 为数字门级模型，非晶体管。未知态结果刻意保守，单步按队列项执行；输入不是原子三元组。实验保存要求稳定状态，传播中的轨迹可以独立导出。所有时间仅为模型 tick。

下一次交付按计划扩展 D 与 C 的多位体验；先复用现有门与事件语义，再设计可组合的多位构造接口，不把本次 builder 固定信号名当作未来层级接口。
