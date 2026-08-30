"""Small event-level debugging surface built only on the public simulator API."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from glassmachine.simulation.engine import Simulation
from glassmachine.trace.events import TraceEvent


@dataclass(frozen=True, slots=True)
class Breakpoint:
    name: str
    predicate: Callable[[TraceEvent], bool]

    @classmethod
    def signal(cls, signal: str) -> Breakpoint:
        return cls(name=f"signal:{signal}", predicate=lambda event: event.signal == signal)


class Debugger:
    def __init__(self, simulation: Simulation) -> None:
        self.simulation = simulation
        self._breakpoints: list[Breakpoint] = []

    def add_breakpoint(self, breakpoint: Breakpoint) -> None:
        self._breakpoints.append(breakpoint)

    def step(self) -> TraceEvent | None:
        while self.simulation.pending_events:
            event = self.simulation.step()
            if event is not None:
                return event
        return None

    def run_until_break(self, *, max_events: int = 10_000) -> tuple[TraceEvent, Breakpoint] | None:
        for _ in range(max_events):
            event = self.step()
            if event is None:
                return None
            for breakpoint in self._breakpoints:
                if breakpoint.predicate(event):
                    return event, breakpoint
        return None

    def probe(self, signal: str) -> tuple[TraceEvent, ...]:
        return self.simulation.trace.for_signal(signal)
