"""Hand-derived path delays and causal chains for the actual five-gate graph."""

import pytest

from glassmachine.models.digital.detailed.full_adder import build_full_adder_simulation
from glassmachine.simulation.engine import Simulation


def prepared(values: str, delay: int) -> Simulation:
    simulation = build_full_adder_simulation(delay=delay)
    for signal, value in zip(("A", "B", "Cin"), values, strict=True):
        simulation.set_input(signal, value)
    simulation.run_until_stable()
    simulation.trace.clear()
    return simulation


def waveform(simulation: Simulation, signal: str) -> list[tuple[int, str, str]]:
    return [
        (e.time, str(e.old_value), str(e.new_value))
        for e in simulation.trace.for_signal(signal)
    ]


def assert_link(simulation: Simulation, child: str, parent: str, delay: int) -> None:
    children = simulation.trace.for_signal(child)
    parents = simulation.trace.for_signal(parent)
    assert len(children) == len(parents)
    for event, cause in zip(children, parents, strict=True):
        assert event.caused_by == cause.event_id
        assert event.time == cause.time + delay
        assert event.delta == (cause.delta + 1 if delay == 0 else 0)


@pytest.mark.parametrize("delay", [0, 1, 3])
@pytest.mark.parametrize("spacing", [0, 1, 3, 4])
def test_short_pulses_traverse_two_xors_without_filtering(delay: int, spacing: int) -> None:
    simulation = prepared("000", delay)
    base = simulation.time + 1
    for index, value in enumerate("1010"):
        simulation.set_input("A", value, at_time=base + spacing * index)
    simulation.run_until_stable()
    # B=Cin=0 makes both XORs identity. Expected waveform is just the
    # submitted pulse train shifted by one and two gate delays, respectively.
    for signal, stages in (("A", 0), ("p", 1), ("Sum", 2)):
        assert waveform(simulation, signal) == [
            (base + index * spacing + stages * delay, old, new)
            for index, (old, new) in enumerate(zip("0101", "1010", strict=True))
        ]
    for signal in ("B", "Cin", "g", "h", "Cout"):
        assert not simulation.trace.for_signal(signal)
    assert_link(simulation, "p", "A", delay)
    assert_link(simulation, "Sum", "p", delay)
    assert simulation.pending_events == 0


@pytest.mark.parametrize("delay", [0, 1, 3])
def test_documented_transition_preserves_carry(delay: int) -> None:
    simulation = prepared("011", delay)
    base = simulation.time + 1
    input_id = simulation.set_input("A", "1", at_time=base)
    simulation.run_until_stable()
    for signal, stages, old, new in (
        ("A", 0, "0", "1"), ("p", 1, "1", "0"), ("g", 1, "0", "1"),
        ("Sum", 2, "0", "1"), ("h", 2, "1", "0"),
    ):
        assert waveform(simulation, signal) == [(base + stages * delay, old, new)]
    assert len(simulation.trace) == 5
    assert simulation.trace.for_signal("g")[0].caused_by == input_id
    assert_link(simulation, "p", "A", delay)
    assert_link(simulation, "Sum", "p", delay)
    assert_link(simulation, "h", "p", delay)
    assert str(simulation.read("Cout")) == "1"


@pytest.mark.parametrize("delay", [0, 2])
def test_carry_input_reaches_cout_via_and_then_or(delay: int) -> None:
    simulation = prepared("010", delay)
    base = simulation.time + 1
    simulation.set_input("Cin", "1", at_time=base)
    simulation.run_until_stable()
    assert waveform(simulation, "Cin") == [(base, "0", "1")]
    assert waveform(simulation, "Sum") == [(base + delay, "1", "0")]
    assert waveform(simulation, "h") == [(base + delay, "0", "1")]
    assert waveform(simulation, "Cout") == [(base + 2 * delay, "0", "1")]
    assert len(simulation.trace) == 4
    assert_link(simulation, "h", "Cin", delay)
    assert_link(simulation, "Sum", "Cin", delay)
    assert_link(simulation, "Cout", "h", delay)


def test_x_to_z_input_does_not_invent_internal_changes() -> None:
    simulation = prepared("X00", 2)
    base = simulation.time + 1
    simulation.set_input("A", "Z", at_time=base)
    simulation.run_until_stable()
    assert waveform(simulation, "A") == [(base, "X", "Z")]
    assert len(simulation.trace) == 1
    assert str(simulation.read("Sum")) == "X"
    assert str(simulation.read("Cout")) == "0"


def test_identical_sequences_have_identical_complete_traces() -> None:
    simulations = [prepared("000", 2) for _ in range(2)]
    for simulation in simulations:
        base = simulation.time + 1
        for index, (signal, value) in enumerate(zip(
            ("A", "B", "Cin", "A", "B", "Cin"), "1X0Z11", strict=True
        )):
            simulation.set_input(signal, value, at_time=base + index)
        simulation.run_until_stable()
    simulations[0].trace.assert_equivalent(simulations[1].trace)


@pytest.mark.parametrize("delay", [0, 2])
@pytest.mark.parametrize("order", [("A", "B"), ("B", "A")])
def test_same_time_input_swap_exposes_reconvergent_hazard(
    delay: int, order: tuple[str, str]
) -> None:
    # Initial 011 and final 101 both total 2, so Sum=0/Cout=1 at both
    # endpoints. Sequential input commits briefly make A==B. Thus p falls
    # then rises at +d, Sum pulses high and h low at +2d, and Cout pulses
    # low at +3d. Fixed transport preserves these same-time transitions.
    # A-first additionally makes A=B=1, pulsing g; B-first makes A=B=0.
    simulation = prepared("011", delay)
    base = simulation.time + 1
    values = {"A": "1", "B": "0"}
    input_ids = [
        simulation.set_input(signal, values[signal], at_time=base) for signal in order
    ]
    simulation.run_until_stable()
    assert [e.signal for e in simulation.trace if e.signal in ("A", "B")] == list(order)
    assert waveform(simulation, "A") == [(base, "0", "1")]
    assert waveform(simulation, "B") == [(base, "1", "0")]
    for signal, stages, first, second in (
        ("p", 1, "1", "0"),
        ("Sum", 2, "0", "1"),
        ("h", 2, "1", "0"),
        ("Cout", 3, "1", "0"),
    ):
        assert waveform(simulation, signal) == [
            (base + stages * delay, first, second),
            (base + stages * delay, second, first),
        ]
    assert [e.caused_by for e in simulation.trace.for_signal("p")] == input_ids
    if order[0] == "A":
        assert waveform(simulation, "g") == [
            (base + delay, "0", "1"), (base + delay, "1", "0")
        ]
        assert [e.caused_by for e in simulation.trace.for_signal("g")] == input_ids
        assert len(simulation.trace) == 12
    else:
        assert not simulation.trace.for_signal("g")
        assert len(simulation.trace) == 10
    assert not simulation.trace.for_signal("Cin")
    assert_link(simulation, "Sum", "p", delay)
    assert_link(simulation, "h", "p", delay)
    assert_link(simulation, "Cout", "h", delay)
    assert str(simulation.read("Sum")) == "0"
    assert str(simulation.read("Cout")) == "1"
