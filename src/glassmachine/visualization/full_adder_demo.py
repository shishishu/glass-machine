"""Full-adder circuit view driven exclusively by the shared controller."""

from __future__ import annotations

from collections.abc import Callable
from itertools import pairwise
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from weakref import ref

from glassmachine.core.errors import GlassMachineError
from glassmachine.core.logic import LogicVector
from glassmachine.models.digital.fast.full_adder import FastFullAdder
from glassmachine.models.digital.reference.full_adder import ReferenceFullAdder
from glassmachine.visualization.full_adder_controller import FullAdderController


def create_full_adder_window() -> Any:
    """Create the optional Qt window; caller owns the QApplication lifecycle."""
    try:
        from PySide6.QtGui import QColor, QPen
        from PySide6.QtWidgets import (
            QComboBox,
            QFileDialog,
            QGraphicsScene,
            QGraphicsView,
            QHBoxLayout,
            QLabel,
            QMainWindow,
            QMessageBox,
            QPushButton,
            QTextEdit,
            QVBoxLayout,
            QWidget,
        )
    except ImportError as exc:
        raise RuntimeError('Install GUI dependencies with pip install "glassmachine[gui]"') from exc

    class FullAdderWindow(QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self.controller = FullAdderController()
            self.setWindowTitle("GlassMachine — M1 一位全加器")
            container = QWidget()
            layout = QVBoxLayout(container)
            layout.addWidget(QLabel("预测 Sum/Cout → 输入入队 → 单步观察 → 运行至稳定并比较"))
            self.status = QLabel()
            self.comparison = QLabel()
            layout.addWidget(self.status)
            layout.addWidget(self.comparison)
            layout.addWidget(
                QLabel("四态结构语义: Z 按未知参与门计算。A=1、B=X、Cin=1 时 Cout=X。")
            )
            self.scene = QGraphicsScene(0, 0, 860, 320, self)
            view = QGraphicsView(self.scene)
            view.setMinimumHeight(350)
            layout.addWidget(view)
            self.wires: list[tuple[str, Any]] = []
            self.labels: dict[str, Any] = {}
            # Wires are bound to source signals; crossings without dots are not junctions.
            paths = {
                "A": [
                    [(30, 60), (120, 60), (120, 90), (210, 90)],
                    [(120, 60), (120, 240), (210, 240)],
                ],
                "B": [
                    [(30, 130), (150, 130), (150, 110), (210, 110)],
                    [(150, 130), (150, 260), (210, 260)],
                ],
                "Cin": [
                    [(30, 300), (390, 300), (390, 110), (450, 110)],
                    [(390, 300), (420, 300), (420, 200), (450, 200)],
                ],
                "p": [
                    [(290, 100), (350, 100), (350, 90), (450, 90)],
                    [(350, 100), (350, 180), (450, 180)],
                ],
                "g": [[(290, 250), (610, 250), (610, 240), (660, 240)]],
                "h": [[(530, 190), (610, 190), (610, 220), (660, 220)]],
                "Sum": [[(530, 100), (810, 100)]],
                "Cout": [[(740, 230), (810, 230)]],
            }
            for signal, branches in paths.items():
                for points in branches:
                    for start, end in pairwise(points):
                        self.wires.append((signal, self.scene.addLine(*start, *end)))
            for x, y, name in [
                (210, 75, "XOR → p"),
                (210, 225, "AND → g"),
                (450, 75, "XOR → Sum"),
                (450, 165, "AND → h"),
                (660, 205, "OR → Cout"),
            ]:
                self.scene.addRect(x, y, 80, 50)
                label = self.scene.addText(name)
                label.setPos(x, y + 12)
            positions = {
                "A": (5, 30),
                "B": (5, 100),
                "Cin": (5, 270),
                "p": (300, 65),
                "g": (300, 250),
                "h": (545, 160),
                "Sum": (755, 65),
                "Cout": (755, 235),
            }
            for signal, pos in positions.items():
                label = self.scene.addText("")
                label.setPos(*pos)
                self.labels[signal] = label
            self.delay_label = self.scene.addText("")
            self.delay_label.setPos(420, 285)
            controls = QHBoxLayout()
            self.inputs: dict[str, Any] = {}
            for signal in ("A", "B", "Cin"):
                controls.addWidget(QLabel(signal))
                selector = QComboBox()
                selector.addItems(["0", "1", "X", "Z"])
                self.inputs[signal] = selector
                controls.addWidget(selector)
            layout.addLayout(controls)
            buttons = QHBoxLayout()
            for button_text, callback in [
                ("输入入队(A→B→Cin)", self.queue_inputs),
                ("单步", self.step),
                ("运行至稳定", self.run),
                ("重置", self.reset),
                ("保存实验", self.save_dialog),
                ("加载并重放", self.load_dialog),
                ("导出轨迹", self.trace_dialog),
            ]:
                button = QPushButton(button_text)
                button.clicked.connect(self._callback(callback.__name__))
                buttons.addWidget(button)
            layout.addLayout(buttons)
            self.events = QTextEdit()
            self.events.setReadOnly(True)
            layout.addWidget(self.events)
            self.setCentralWidget(container)
            self.resize(1080, 720)
            self.refresh()

        def _callback(self, name: str) -> Callable[[bool], None]:
            # Qt owns each button; its callback must not keep the whole window alive.
            receiver = ref(self)

            def trigger(_checked: bool = False) -> None:
                window = receiver()
                if window is not None:
                    window.perform(getattr(window, name))

            return trigger

        def perform(self, operation: Callable[[], None]) -> None:
            try:
                operation()
            except (GlassMachineError, OSError, ValueError) as exc:
                QMessageBox.warning(self, "操作未完成", str(exc))
            self.refresh()

        def queue_inputs(self) -> None:
            for signal in ("A", "B", "Cin"):
                self.controller.queue(signal, self.inputs[signal].currentText())
            self.refresh()

        def step(self) -> None:
            self.controller.step()
            self.refresh()

        def run(self) -> None:
            self.controller.run()
            self.refresh()

        def reset(self) -> None:
            self.controller.reset()
            self.refresh()

        def save_dialog(self) -> None:
            path, _ = QFileDialog.getSaveFileName(
                self, "保存稳定态实验", "full-adder.json", "JSON (*.json)"
            )
            if path:
                self.controller.save(path)

        def load_dialog(self) -> None:
            path, _ = QFileDialog.getOpenFileName(self, "加载并验证实验", "", "JSON (*.json)")
            if path:
                self.controller.load(path)
                for signal, selector in self.inputs.items():
                    selector.setCurrentText(str(self.controller.simulation.read(signal)))

        def trace_dialog(self) -> None:
            path, _ = QFileDialog.getSaveFileName(
                self, "导出当前已提交轨迹", "full-adder.jsonl", "JSONL (*.jsonl)"
            )
            if path:
                self.controller.export_trace(path)

        def refresh(self) -> None:
            simulation = self.controller.simulation
            values = simulation.signal_values()
            self.delay_label.setPlainText(
                f"连线交叉不表示连接;同名信号为同一网络。门延迟 = {self.controller.delay} tick"
            )
            colors = {"0": "#64748b", "1": "#16a34a", "X": "#d97706", "Z": "#9333ea"}
            self.status.setText(
                f"模型时间 {simulation.time} | 待处理 {simulation.pending_events} | "
                "输入逐个提交,不保证原子更新;单步可能仅消费无变化项。"
            )
            for signal, label in self.labels.items():
                label.setPlainText(f"{signal} = {values[signal]}")
            for signal, wire in self.wires:
                wire.setPen(QPen(QColor(colors[str(values[signal])]), 2))
            if simulation.pending_events:
                self.comparison.setText("传播中:暂不进行稳定态三模型比较。")
            else:
                args = tuple(LogicVector.parse(values[name]) for name in ("A", "B", "Cin"))
                reference = ReferenceFullAdder().evaluate(*args)
                fast = FastFullAdder().evaluate(*args)
                actual = (values["Sum"], values["Cout"])
                passed = actual == (reference.sum, reference.carry) == (fast.sum, fast.carry)
                self.comparison.setText(
                    f"稳定态比较 {'PASS' if passed else 'FAIL'} | "
                    f"Reference {reference.sum}/{reference.carry} | "
                    f"Detailed {actual[0]}/{actual[1]} | Fast {fast.sum}/{fast.carry}(Sum/Cout)"
                )
            self.events.setPlainText(
                "\n".join(
                    f"t={e.time} Δ={e.delta} #{e.event_id} {e.signal}: "
                    f"{e.old_value}→{e.new_value} cause={e.caused_by}"
                    for e in simulation.trace
                )
            )

    return FullAdderWindow()


def run_full_adder_demo(*, smoke: bool = False) -> int:
    try:
        from PySide6.QtCore import QCoreApplication, QEvent, QTimer
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise RuntimeError('Install GUI dependencies with pip install "glassmachine[gui]"') from exc
    application = QApplication.instance() or QApplication([])
    window = create_full_adder_window()
    try:
        window.show()
        if smoke:
            # Exercise actual widget/controller paths, not only window construction.
            window.inputs["A"].setCurrentText("1")
            window.inputs["B"].setCurrentText("1")
            window.queue_inputs()
            window.step()
            window.run()
            assert str(window.controller.simulation.read("Sum")) == "0"
            assert str(window.controller.simulation.read("Cout")) == "1"
            with TemporaryDirectory() as directory:
                path = Path(directory) / "record.json"
                window.controller.save(path)
                window.reset()
                window.controller.load(path)
                window.refresh()
                assert "PASS" in window.comparison.text()
            QTimer.singleShot(50, application.quit)
        return application.exec()
    finally:
        # Destroy the complete QObject tree while QApplication is still alive.
        # Deferring this to Python interpreter teardown can destroy scene/view wrappers
        # in an unsafe order, particularly after the event loop has already stopped.
        window.close()
        window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
