"""Headless controller shared by the GUI and integration tests."""

from __future__ import annotations

from dataclasses import dataclass

from glassmachine.core.logic import LogicValue
from glassmachine.models.digital.detailed.not_gate import build_not_simulation
from glassmachine.trace.events import TraceEvent


@dataclass(frozen=True, slots=True)
class NotDemoState:
    input_value: str
    output_value: str
    time: int
    trace_digest: str


class NotDemoController:
    """Controls simulation only; it contains no drawing state."""

    def __init__(self, *, delay: int = 1) -> None:
        self._delay = delay
        self.simulation = build_not_simulation(delay=delay)

    @property
    def state(self) -> NotDemoState:
        return NotDemoState(
            input_value=str(self.simulation.read("input")),
            output_value=str(self.simulation.read("output")),
            time=self.simulation.time,
            trace_digest=self.simulation.trace.digest(),
        )

    def apply(self, value: str | LogicValue) -> tuple[TraceEvent, ...]:
        self.simulation.set_input("input", value, reason="NOT demo control")
        return self.simulation.run_until_stable()

    def reset(self) -> NotDemoState:
        self.simulation = build_not_simulation(delay=self._delay)
        return self.state
