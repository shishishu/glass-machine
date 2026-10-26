"""Headless full-adder interaction; rendering never owns circuit state."""

from __future__ import annotations

from pathlib import Path

from glassmachine.core.errors import ConfigurationError
from glassmachine.core.logic import LogicValue
from glassmachine.experiments.full_adder import (
    AdderAction,
    AdderAdvance,
    AdderInput,
    FullAdderExperiment,
    FullAdderRecord,
    apply_action,
)
from glassmachine.models.digital.detailed.full_adder import build_full_adder_simulation


class FullAdderController:
    def __init__(self, *, delay: int = 1) -> None:
        FullAdderExperiment((), delay)
        self.delay = delay
        self.reset()

    def reset(self) -> None:
        self.simulation = build_full_adder_simulation(delay=self.delay)
        self.base = self.simulation.time
        self.simulation.trace.clear()
        self.actions: list[AdderAction] = []

    def _apply(self, action: AdderAction) -> None:
        apply_action(self.simulation, action, self.base, len(self.actions))
        self.actions.append(action)

    def queue(self, signal: str, value: str | LogicValue, *, time: int | None = None) -> None:
        relative = self.simulation.time - self.base if time is None else time
        self._apply(AdderInput(relative, signal, LogicValue.parse(value)))

    def step(self) -> None:
        self._apply(AdderAdvance("step"))

    def run(self) -> None:
        self._apply(AdderAdvance("run"))

    def save(self, path: str | Path) -> None:
        if self.simulation.pending_events:
            raise ConfigurationError("run to stable before saving an experiment")
        experiment = FullAdderExperiment(tuple(self.actions), self.delay)
        record = FullAdderRecord(
            experiment,
            self.simulation.trace.events,
            str(self.simulation.read("Sum")),
            str(self.simulation.read("Cout")),
        )
        record.replay()  # Verify the exact displayed execution is reproducible before writing.
        record.write_json(path)

    def load(self, path: str | Path) -> None:
        record = FullAdderRecord.read_json(path)
        simulation = record.replay()
        # Records finish by draining the queue. Preserve that boundary for later input actions.
        actions = [*record.experiment.actions, AdderAdvance("run")]
        base = build_full_adder_simulation(delay=record.experiment.delay).time
        self.delay = record.experiment.delay
        self.simulation = simulation
        self.actions = actions
        self.base = base

    def export_trace(self, path: str | Path) -> None:
        self.simulation.trace.write_jsonl(path)
