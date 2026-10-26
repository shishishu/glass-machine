"""Actual optional Qt interactions; skipped in core-only installations."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox, QPushButton

from glassmachine.trace.trace import Trace
from glassmachine.visualization.full_adder_controller import FullAdderController
from glassmachine.visualization.full_adder_demo import create_full_adder_window


@pytest.fixture
def window():
    app = QApplication.instance() or QApplication([])
    widget = create_full_adder_window()
    widget.show()
    app.processEvents()
    yield widget
    widget.close()
    app.processEvents()


def click(window, text):
    button = next(b for b in window.findChildren(QPushButton) if b.text() == text)
    button.click()
    QApplication.processEvents()


def test_widgets_queue_step_run_and_show_real_internal_values(window):
    for signal, value in zip(("A", "B", "Cin"), "011", strict=True):
        window.inputs[signal].setCurrentText(value)
    click(window, "输入入队(A→B→Cin)")
    assert window.controller.simulation.pending_events == 3
    assert "传播中" in window.comparison.text()
    click(window, "单步")
    assert str(window.controller.simulation.read("A")) == "0"
    click(window, "运行至稳定")
    assert "PASS" in window.comparison.text()
    for signal, label in window.labels.items():
        assert label.toPlainText() == f"{signal} = {window.controller.simulation.read(signal)}"
    assert str(window.controller.simulation.read("Sum")) == "0"
    assert str(window.controller.simulation.read("Cout")) == "1"
    assert "cause=" in window.events.toPlainText()
    window.inputs["A"].setCurrentText("1")
    click(window, "输入入队(A→B→Cin)")
    click(window, "运行至稳定")
    assert str(window.controller.simulation.read("Sum")) == "1"
    assert str(window.controller.simulation.read("Cout")) == "1"


def test_save_load_and_export_dialogs_roundtrip_actual_trace(window, monkeypatch, tmp_path):
    window.inputs["A"].setCurrentText("1")
    window.inputs["B"].setCurrentText("X")
    window.inputs["Cin"].setCurrentText("1")
    click(window, "输入入队(A→B→Cin)")
    click(window, "运行至稳定")
    assert str(window.controller.simulation.read("Cout")) == "X"
    assert "PASS" in window.comparison.text()
    expected = Trace(window.controller.simulation.trace.events)
    record = tmp_path / "record.json"
    trace = tmp_path / "trace.jsonl"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *a, **k: (str(record), ""))
    click(window, "保存实验")
    assert record.exists()
    click(window, "重置")
    assert len(window.controller.simulation.trace) == 0
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(record), ""))
    click(window, "加载并重放")
    expected.assert_equivalent(window.controller.simulation.trace)
    assert window.inputs["B"].currentText() == "X"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *a, **k: (str(trace), ""))
    click(window, "导出轨迹")
    expected.assert_equivalent(Trace.read_jsonl(trace))


def test_pending_save_and_bad_record_show_error_without_losing_state(
    window, monkeypatch, tmp_path
):
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args[2]))
    path = tmp_path / "record.json"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *a, **k: (str(path), ""))
    click(window, "输入入队(A→B→Cin)")
    click(window, "保存实验")
    assert warnings and "stable" in warnings[-1]
    assert not path.exists()
    click(window, "运行至稳定")
    expected = Trace(window.controller.simulation.trace.events)
    path.write_text('{"kind":"full-adder"}')
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(path), ""))
    click(window, "加载并重放")
    assert len(warnings) == 2
    expected.assert_equivalent(window.controller.simulation.trace)


def test_loaded_delay_is_shown_in_diagram(window, monkeypatch, tmp_path):
    controller = FullAdderController(delay=3)
    controller.queue("A", "0")
    controller.run()
    path = tmp_path / "delay.json"
    controller.save(path)
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(path), ""))
    click(window, "加载并重放")
    assert window.controller.delay == 3
    assert "3 tick" in window.delay_label.toPlainText()
