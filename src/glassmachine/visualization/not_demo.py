"""Minimal PySide6 view for the M0 NOT simulation."""

from __future__ import annotations

from glassmachine.core.logic import LogicValue
from glassmachine.visualization.controller import NotDemoController


def run_not_demo(*, smoke: bool = False) -> int:
    try:
        from PySide6.QtCore import Qt, QTimer
        from PySide6.QtGui import QColor, QPen
        from PySide6.QtWidgets import (
            QApplication,
            QGraphicsEllipseItem,
            QGraphicsLineItem,
            QGraphicsRectItem,
            QGraphicsScene,
            QGraphicsSimpleTextItem,
            QGraphicsView,
            QHBoxLayout,
            QLabel,
            QMainWindow,
            QPushButton,
            QTextEdit,
            QVBoxLayout,
            QWidget,
        )
    except ImportError as exc:  # pragma: no cover - depends on optional system GUI
        raise RuntimeError(
            'PySide6 is required for the GUI; install with: pip install "glassmachine[gui]"'
        ) from exc

    class NotWindow(QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self.controller = NotDemoController(delay=1)
            self.setWindowTitle("GlassMachine — M0 NOT")

            container = QWidget()
            layout = QVBoxLayout(container)
            self.status = QLabel()
            self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.status)

            self.scene = QGraphicsScene(0, 0, 520, 180)
            self.view = QGraphicsView(self.scene)
            self.view.setMinimumHeight(210)
            layout.addWidget(self.view)
            self._build_diagram(
                QGraphicsRectItem,
                QGraphicsEllipseItem,
                QGraphicsLineItem,
                QGraphicsSimpleTextItem,
                QPen,
            )

            controls = QHBoxLayout()
            for value in LogicValue:
                button = QPushButton(f"Input {value.value}")
                button.clicked.connect(lambda _checked=False, selected=value: self.apply(selected))
                controls.addWidget(button)
            layout.addLayout(controls)

            self.events = QTextEdit()
            self.events.setReadOnly(True)
            self.events.setPlaceholderText("Committed simulation events")
            layout.addWidget(self.events)

            self.setCentralWidget(container)
            self.resize(680, 520)
            self.refresh()

        def _build_diagram(self, rect_type, ellipse_type, line_type, text_type, pen_type) -> None:
            self.input_node = ellipse_type(45, 72, 36, 36)
            self.gate = rect_type(210, 50, 110, 80)
            self.output_node = ellipse_type(440, 72, 36, 36)
            self.input_wire = line_type(81, 90, 210, 90)
            self.output_wire = line_type(320, 90, 440, 90)
            for item in (
                self.input_node,
                self.gate,
                self.output_node,
                self.input_wire,
                self.output_wire,
            ):
                self.scene.addItem(item)
            gate_label = text_type("NOT")
            gate_label.setPos(250, 80)
            input_label = text_type("input")
            input_label.setPos(43, 120)
            output_label = text_type("output")
            output_label.setPos(430, 120)
            for label in (gate_label, input_label, output_label):
                self.scene.addItem(label)
            self._pen_type = pen_type

        def apply(self, value: LogicValue) -> None:
            committed = self.controller.apply(value)
            for event in committed:
                self.events.append(
                    f"t={event.time} Δ={event.delta} #{event.event_id} "
                    f"{event.signal}: {event.old_value}→{event.new_value} "
                    f"cause={event.caused_by}"
                )
            self.refresh()

        def refresh(self) -> None:
            state = self.controller.state
            self.status.setText(
                f"Input {state.input_value}  →  NOT  →  Output {state.output_value}  "
                f"(simulation time {state.time})"
            )
            input_color = self._color(state.input_value, QColor)
            output_color = self._color(state.output_value, QColor)
            self.input_node.setBrush(input_color)
            self.output_node.setBrush(output_color)
            self.input_wire.setPen(self._pen_type(input_color, 4))
            self.output_wire.setPen(self._pen_type(output_color, 4))

        @staticmethod
        def _color(value: str, color_type):
            return {
                "0": color_type("#64748b"),
                "1": color_type("#22c55e"),
                "X": color_type("#f59e0b"),
                "Z": color_type("#a855f7"),
            }[value]

    application = QApplication.instance() or QApplication([])
    window = NotWindow()
    window.show()
    if smoke:
        QTimer.singleShot(50, application.quit)
    return application.exec()
