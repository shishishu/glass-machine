"""Auditable one-bit NOT gate for the M0 detailed-model vertical slice."""

from collections.abc import Mapping

from glassmachine.core.component import Component, Port, PortDirection
from glassmachine.core.errors import SimulationError
from glassmachine.core.logic import LogicValue, LogicVector
from glassmachine.simulation.engine import Simulation


class NotGate(Component):
    def __init__(
        self,
        component_id: str,
        *,
        input_signal: str,
        output_signal: str,
        delay: int = 1,
    ) -> None:
        super().__init__(
            component_id,
            ports=(
                Port("in", PortDirection.INPUT, 1),
                Port("out", PortDirection.OUTPUT, 1),
            ),
            bindings={"in": input_signal, "out": output_signal},
            delay=delay,
        )

    def evaluate(self, inputs: Mapping[str, LogicVector]) -> Mapping[str, LogicVector]:
        try:
            bit = inputs["in"].require_width(1, context=f"{self.component_id}.in").scalar
        except KeyError as exc:
            raise SimulationError(f"{self.component_id!r} requires input port 'in'") from exc
        if bit is LogicValue.ZERO:
            output = LogicValue.ONE
        elif bit is LogicValue.ONE:
            output = LogicValue.ZERO
        else:
            output = LogicValue.UNKNOWN
        return {"out": LogicVector.bit(output)}


def build_not_simulation(*, delay: int = 1) -> Simulation:
    simulation = Simulation()
    simulation.add_signal("input", width=1, initial="Z", external=True)
    simulation.add_signal("output", width=1, initial="Z")
    simulation.add_component(
        NotGate("not", input_signal="input", output_signal="output", delay=delay)
    )
    simulation.initialize()
    simulation.run_until_stable()
    return simulation
