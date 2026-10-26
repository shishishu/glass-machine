"""User task regressions: interactive replay, errors and CLI compatibility."""

import json
from dataclasses import replace

import pytest

from glassmachine.cli import main
from glassmachine.core.errors import ConfigurationError, ReplayMismatchError
from glassmachine.experiments.full_adder import FullAdderRecord
from glassmachine.visualization.full_adder_controller import FullAdderController


def test_interactive_sequence_replays_exact_trace_and_can_continue(tmp_path):
    controller = FullAdderController(delay=2)
    controller.queue("A", "1")
    controller.step()
    controller.queue("B", "1")
    controller.step()
    controller.queue("Cin", "0")
    controller.run()
    assert str(controller.simulation.read("Sum")) == "0"
    assert str(controller.simulation.read("Cout")) == "1"
    path = tmp_path / "interactive.json"
    controller.save(path)
    expected = controller.simulation.trace
    loaded = FullAdderController()
    loaded.load(path)
    expected.assert_equivalent(loaded.simulation.trace)
    loaded.queue("Cin", "1")
    loaded.run()
    assert str(loaded.simulation.read("Sum")) == "1"
    loaded.save(path)
    FullAdderRecord.read_json(path).replay().trace.assert_equivalent(loaded.simulation.trace)


def test_pending_save_rejected_and_trace_still_exportable(tmp_path):
    controller = FullAdderController()
    controller.queue("A", "0")
    controller.step()
    with pytest.raises(ConfigurationError, match="stable"):
        controller.save(tmp_path / "pending.json")
    controller.export_trace(tmp_path / "partial.jsonl")
    assert (tmp_path / "partial.jsonl").exists()
    assert not (tmp_path / "pending.json").exists()


def test_replay_reports_first_changed_event(tmp_path):
    controller = FullAdderController()
    controller.queue("A", "1")
    controller.run()
    path = tmp_path / "record.json"
    controller.save(path)
    record = FullAdderRecord.read_json(path)
    events = (replace(record.expected_events[0], time=999), *record.expected_events[1:])
    with pytest.raises(ReplayMismatchError, match="event index 0"):
        replace(record, expected_events=events).replay()


@pytest.mark.parametrize("bad_time", [-1, True, 1.5, "0"])
def test_record_rejects_non_integer_or_negative_input_time(tmp_path, bad_time):
    controller = FullAdderController()
    controller.queue("A", "1")
    controller.run()
    path = tmp_path / "bad.json"
    controller.save(path)
    payload = json.loads(path.read_text())
    payload["config"]["actions"][0]["time"] = bad_time
    path.write_text(json.dumps(payload))
    with pytest.raises(ConfigurationError):
        FullAdderRecord.read_json(path)


def test_failed_load_does_not_replace_current_circuit(tmp_path):
    controller = FullAdderController()
    controller.queue("A", "1")
    controller.run()
    simulation = controller.simulation
    path = tmp_path / "bad.json"
    path.write_text("[]")
    with pytest.raises(ReplayMismatchError):
        controller.load(path)
    assert controller.simulation is simulation


def test_cli_adder_save_replay_and_bad_record(tmp_path, capsys):
    path = tmp_path / "record.json"
    trace = tmp_path / "trace.jsonl"
    assert (
        main(
            [
                "full-adder",
                "--a",
                "1",
                "--b",
                "1",
                "--cin",
                "0",
                "--record",
                str(path),
                "--trace",
                str(trace),
            ]
        )
        == 0
    )
    assert "Sum=0 Cout=1" in capsys.readouterr().out
    assert main(["replay", str(path)]) == 0
    assert "replay: PASS" in capsys.readouterr().out
    assert main(["verify", "--model", "full-adder"]) == 0
    assert "64 four-state" in capsys.readouterr().out
    path.write_text("[]")
    assert main(["replay", str(path)]) == 2
    assert "error:" in capsys.readouterr().err
    assert main(["full-adder", "--delay", "-1"]) == 2


@pytest.mark.parametrize(
    "field,value",
    [("time", "1"), ("width", 2), ("old_value", "00"), ("caused_by", True), ("reason", [])],
)
def test_record_rejects_malformed_event(tmp_path, field, value):
    controller = FullAdderController()
    controller.queue("A", "1")
    controller.run()
    path = tmp_path / "bad-event.json"
    controller.save(path)
    payload = json.loads(path.read_text())
    payload["expected_events"][0][field] = value
    path.write_text(json.dumps(payload))
    with pytest.raises(ReplayMismatchError):
        FullAdderRecord.read_json(path)
