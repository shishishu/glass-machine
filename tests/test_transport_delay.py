"""固定传输延迟。以真值表和时间平移独立检查完整波形。"""

from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from glassmachine.experiments.not_gate import ExperimentRecord
from glassmachine.models.digital.detailed.not_gate import NotGate, build_not_simulation
from glassmachine.simulation.engine import Simulation

TRUTH = {"0": "1", "1": "0", "X": "X", "Z": "X"}


def check_waveform(
    *, delay: int, initial: str, requests: list[tuple[int, str]]
) -> Simulation:
    simulation = build_not_simulation(delay=delay)
    simulation.set_input("input", initial)
    simulation.run_until_stable()
    simulation.trace.clear()
    base = simulation.time + 1
    expected_inputs = []
    expected_outputs = []
    previous_input = initial
    previous_output = TRUTH[initial]

    # 预期只依赖请求、字面真值表和时间平移。不读取实际输出轨迹。
    for offset, value in requests:
        time = base + offset
        input_id = simulation.set_input("input", value, at_time=time)
        if value == previous_input:
            continue
        expected_inputs.append((time, previous_input, value, input_id))
        proposed = TRUTH[value]
        if proposed != previous_output:
            expected_outputs.append((time + delay, previous_output, proposed, input_id))
            previous_output = proposed
        previous_input = value

    simulation.run_until_stable()
    inputs = simulation.trace.for_signal("input")
    outputs = simulation.trace.for_signal("output")
    assert [(e.time, str(e.old_value), str(e.new_value), e.event_id) for e in inputs] == (
        expected_inputs
    )
    assert [(e.time, str(e.old_value), str(e.new_value), e.caused_by) for e in outputs] == (
        expected_outputs
    )
    by_id = {e.event_id: e for e in inputs}
    for event in outputs:
        cause = by_id[event.caused_by]
        assert event.source_component == "not"
        assert event.source_port == "out"
        assert event.time == cause.time + delay
        assert event.delta == (cause.delta + 1 if delay == 0 else 0)
    assert str(simulation.read("output")) == TRUTH[previous_input]
    assert simulation.pending_events == 0
    return simulation


@pytest.mark.parametrize("spacing", [1, 3, 4])
@pytest.mark.parametrize("values", ["01", "010"])
def test_pulses_shorter_equal_and_longer_than_delay(spacing: int, values: str) -> None:
    # "010" 的旧实现最终值正确但中间波形错误。必须比较完整序列。
    check_waveform(
        delay=3,
        initial="1",
        requests=[(i * spacing, value) for i, value in enumerate(values)],
    )


@pytest.mark.parametrize("delay", [0, 3])
def test_same_time_inputs_follow_submission_order(delay: int) -> None:
    check_waveform(delay=delay, initial="1", requests=[(0, v) for v in "0101"])


@pytest.mark.parametrize("delay", [0, 3])
def test_repeated_and_unknown_inputs_do_not_invent_output_changes(delay: int) -> None:
    check_waveform(
        delay=delay, initial="1", requests=list(enumerate("00XXZZX110"))
    )


@settings(max_examples=200, derandomize=True)
@given(
    delay=st.integers(min_value=0, max_value=5),
    initial=st.sampled_from(tuple(TRUTH)),
    changes=st.lists(
        st.tuples(st.integers(min_value=0, max_value=5), st.sampled_from(tuple(TRUTH))),
        min_size=1,
        max_size=20,
    ),
)
def test_four_state_sequences_match_time_shift_oracle(delay, initial, changes) -> None:
    offset = 0
    requests = []
    for gap, value in changes:
        offset += gap
        requests.append((offset, value))
    check_waveform(delay=delay, initial=initial, requests=requests)


@pytest.mark.parametrize("delays", [(2, 3), (0, 0), (0, 3), (3, 0)])
def test_two_not_gates_preserve_pulses_and_causal_chain(delays: tuple[int, int]) -> None:
    first_delay, second_delay = delays
    simulation = Simulation()
    simulation.add_signal("input", initial="1", external=True)
    simulation.add_signal("middle", initial="0")
    simulation.add_signal("output", initial="1")
    simulation.add_component(
        NotGate("first", input_signal="input", output_signal="middle", delay=first_delay)
    )
    simulation.add_component(
        NotGate("second", input_signal="middle", output_signal="output", delay=second_delay)
    )
    simulation.initialize()
    simulation.run_until_stable()
    simulation.trace.clear()
    base = simulation.time + 1
    input_ids = [
        simulation.set_input("input", value, at_time=base + index)
        for index, value in enumerate("0101")
    ]
    simulation.run_until_stable()
    middle = simulation.trace.for_signal("middle")
    output = simulation.trace.for_signal("output")
    assert [(e.time, str(e.new_value), e.caused_by) for e in middle] == [
        (base + i + first_delay, value, input_ids[i]) for i, value in enumerate("1010")
    ]
    assert [(e.time, str(e.new_value), e.caused_by) for e in output] == [
        (base + i + first_delay + second_delay, value, middle[i].event_id)
        for i, value in enumerate("0101")
    ]
    assert str(simulation.read("output")) == "1"


def test_noop_step_advances_time_without_trace_or_downstream_event() -> None:
    simulation = build_not_simulation(delay=3)
    simulation.trace.clear()
    input_id = simulation.set_input("input", "X")  # Z→X 但 NOT 仍为 X。
    event = simulation.step()
    assert event is not None and event.event_id == input_id
    assert simulation.pending_events == 1
    input_time = simulation.time
    assert simulation.step() is None
    assert simulation.time == input_time + 3
    assert len(simulation.trace) == 1
    assert simulation.pending_events == 0


def test_rapid_sequence_is_deterministic() -> None:
    requests = list(enumerate("01XZ0101"))
    left = check_waveform(delay=3, initial="1", requests=requests)
    right = check_waveform(delay=3, initial="1", requests=requests)
    left.trace.assert_equivalent(right.trace)


def test_original_experiment_record_still_replays() -> None:
    path = Path(__file__).resolve().parents[1] / "experiments" / "m0-not.json"
    record = ExperimentRecord.read_json(path)
    result = record.replay()
    assert str(result.output) == "X"


def test_short_pulse_record_matches_literal_waveform_and_replays() -> None:
    path = Path(__file__).resolve().parents[1] / "experiments" / "m0-not-short-pulse.json"
    record = ExperimentRecord.read_json(path)
    result = record.experiment.run()
    # 初始传播结束于 t=3。配置时间相对于此时刻。
    assert [(e.time, str(e.new_value)) for e in result.trace.for_signal("output")] == [
        (6, "0"), (10, "1"), (11, "0"), (12, "1")
    ]
    result.trace.assert_equivalent(record.replay().trace)
