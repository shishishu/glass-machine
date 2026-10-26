"""Half/full adders assembled from real event-driven gate components."""

from glassmachine.models.digital.detailed.gates import AndGate, OrGate, XorGate
from glassmachine.simulation.engine import Simulation


def build_half_adder_simulation(*, delay: int = 1) -> Simulation:
    simulation = Simulation()
    for name in ("A", "B", "Sum", "Cout"):
        simulation.add_signal(name, initial="Z", external=name in ("A", "B"))
    simulation.add_component(
        XorGate("sum", input_a="A", input_b="B", output_signal="Sum", delay=delay)
    )
    simulation.add_component(
        AndGate("carry", input_a="A", input_b="B", output_signal="Cout", delay=delay)
    )
    simulation.initialize()
    simulation.run_until_stable()
    return simulation


def build_full_adder_simulation(*, delay: int = 1) -> Simulation:
    simulation = Simulation()
    for name in ("A", "B", "Cin", "p", "g", "h", "Sum", "Cout"):
        simulation.add_signal(name, initial="Z", external=name in ("A", "B", "Cin"))
    for gate_type, name, a, b, output in (
        (XorGate, "propagate", "A", "B", "p"),
        (AndGate, "generate", "A", "B", "g"),
        (XorGate, "sum", "p", "Cin", "Sum"),
        (AndGate, "carry_enable", "p", "Cin", "h"),
        (OrGate, "carry", "g", "h", "Cout"),
    ):
        simulation.add_component(
            gate_type(name, input_a=a, input_b=b, output_signal=output, delay=delay)
        )
    simulation.initialize()
    simulation.run_until_stable()
    return simulation
