"""Independent review regressions for action replay and state preservation."""

import json
import random

import pytest

from glassmachine.core.errors import ConfigurationError, ReplayMismatchError
from glassmachine.experiments.full_adder import FullAdderRecord
from glassmachine.visualization.full_adder_controller import FullAdderController


@pytest.mark.parametrize("delay", [0, 1, 3])
def test_mixed_step_run_and_future_input_roundtrips(tmp_path, delay):
    rng = random.Random(1911)
    controller = FullAdderController(delay=delay)
    path = tmp_path / "mixed.json"
    for batch in range(6):
        for _ in range(30):
            action = rng.randrange(4)
            if action < 2:
                offset = controller.simulation.time - controller.base + rng.randrange(4)
                controller.queue(rng.choice(("A", "B", "Cin")), rng.choice("01XZ"), time=offset)
            elif action == 2:
                controller.step()
            else:
                controller.run()
        controller.run()
        before = controller.simulation
        actions = tuple(controller.actions)
        controller.save(path)
        assert controller.simulation is before
        assert tuple(controller.actions) == actions
        replay = FullAdderRecord.read_json(path).replay()
        before.trace.assert_equivalent(replay.trace)
        assert before.signal_values() == replay.signal_values()
        assert (before.time, before.delta, before.pending_events) == (
            replay.time, replay.delta, replay.pending_events
        )
        controller.load(path)
        assert controller.simulation.signal_values() == before.signal_values(), batch


def test_noop_input_time_survives_load_and_resume(tmp_path):
    controller = FullAdderController(delay=2)
    controller.queue("A", "Z", time=100)  # unchanged input still advances time
    controller.run()
    assert not controller.simulation.trace.events
    saved_time = controller.simulation.time
    path = tmp_path / "noop.json"
    controller.save(path)
    controller.load(path)
    assert controller.simulation.time == saved_time
    controller.queue("A", "0")
    controller.step()
    assert controller.simulation.trace.events[0].time == saved_time
    controller.run()
    controller.save(path)
    FullAdderRecord.read_json(path).replay().trace.assert_equivalent(controller.simulation.trace)


def test_bad_replay_and_past_input_preserve_controller_state(tmp_path):
    controller = FullAdderController(delay=3)
    controller.queue("A", "0")
    controller.run()
    path = tmp_path / "bad.json"
    controller.save(path)
    state = controller.simulation
    actions = tuple(controller.actions)
    values = state.signal_values()
    digest = state.trace.digest()
    payload = json.loads(path.read_text())
    payload["expected_events"][0]["time"] += 1
    path.write_text(json.dumps(payload))
    with pytest.raises(ReplayMismatchError):
        controller.load(path)
    assert controller.simulation is state
    assert tuple(controller.actions) == actions
    with pytest.raises(ConfigurationError):
        controller.queue("B", "1", time=0)
    assert tuple(controller.actions) == actions
    assert state.signal_values() == values
    assert state.trace.digest() == digest
