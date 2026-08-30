import unittest

from glassmachine.core.component import Component, Port, PortDirection
from glassmachine.core.errors import ConfigurationError, SimulationError, UnstableSimulationError
from glassmachine.core.logic import LogicVector
from glassmachine.models.digital.not_gate import NotGate, build_not_simulation
from glassmachine.simulation.engine import Simulation


class BadWidthComponent(Component):
    def __init__(self) -> None:
        super().__init__(
            "wide",
            ports=(
                Port("in", PortDirection.INPUT, 2),
                Port("out", PortDirection.OUTPUT, 1),
            ),
            bindings={"in": "input", "out": "output"},
        )

    def evaluate(self, inputs):
        return {"out": LogicVector.bit("0")}


class SimulationTests(unittest.TestCase):
    def test_not_commits_a_causal_delayed_event(self) -> None:
        simulation = build_not_simulation(delay=3)
        simulation.trace.clear()
        input_event_id = simulation.set_input("input", "0")
        committed = simulation.run_until_stable()

        self.assertEqual(str(simulation.read("output")), "1")
        self.assertEqual(len(committed), 2)
        input_event, output_event = committed
        self.assertEqual(input_event.event_id, input_event_id)
        self.assertEqual(output_event.caused_by, input_event.event_id)
        self.assertEqual(output_event.time, input_event.time + 3)

    def test_same_run_is_deterministic(self) -> None:
        digests = []
        for _ in range(2):
            simulation = build_not_simulation(delay=1)
            simulation.trace.clear()
            for at_time, value in ((2, "0"), (4, "1"), (6, "X"), (8, "Z")):
                simulation.set_input("input", value, at_time=at_time)
            simulation.run_until_stable()
            digests.append(simulation.trace.digest())
        self.assertEqual(digests[0], digests[1])

    def test_snapshot_restore_recovers_stable_state(self) -> None:
        simulation = build_not_simulation(delay=1)
        snapshot = simulation.snapshot()
        simulation.set_input("input", "0")
        simulation.run_until_stable()
        self.assertEqual(str(simulation.read("output")), "1")

        simulation.restore(snapshot)
        self.assertEqual(str(simulation.read("input")), "Z")
        self.assertEqual(str(simulation.read("output")), "X")
        self.assertEqual(len(simulation.trace), 0)

    def test_snapshot_requires_a_stable_queue(self) -> None:
        simulation = build_not_simulation()
        simulation.set_input("input", "0")
        with self.assertRaises(SimulationError):
            simulation.snapshot()

    def test_external_input_width_is_checked(self) -> None:
        simulation = build_not_simulation()
        with self.assertRaises(ConfigurationError):
            simulation.set_input("input", "01")

    def test_non_external_signal_cannot_be_driven_from_api(self) -> None:
        simulation = build_not_simulation()
        with self.assertRaises(ConfigurationError):
            simulation.set_input("output", "0")

    def test_duplicate_driver_is_rejected(self) -> None:
        simulation = Simulation()
        simulation.add_signal("a", external=True)
        simulation.add_signal("b", external=True)
        simulation.add_signal("out")
        simulation.add_component(NotGate("not_a", input_signal="a", output_signal="out"))
        with self.assertRaises(ConfigurationError):
            simulation.add_component(NotGate("not_b", input_signal="b", output_signal="out"))

    def test_binding_width_mismatch_is_rejected(self) -> None:
        simulation = Simulation()
        simulation.add_signal("input", width=1, external=True)
        simulation.add_signal("output", width=1)
        with self.assertRaises(ConfigurationError):
            simulation.add_component(BadWidthComponent())

    def test_graph_is_frozen_after_initialization(self) -> None:
        simulation = build_not_simulation()
        with self.assertRaises(ConfigurationError):
            simulation.add_signal("late")

    def test_zero_delay_oscillation_hits_the_event_budget(self) -> None:
        simulation = Simulation()
        simulation.add_signal("a", initial="0")
        simulation.add_component(
            NotGate("not_a", input_signal="a", output_signal="a", delay=0)
        )
        simulation.initialize()
        with self.assertRaises(UnstableSimulationError):
            simulation.run_until_stable(max_events=20)


if __name__ == "__main__":
    unittest.main()
