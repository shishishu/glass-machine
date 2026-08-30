"""Serializable, reproducible M0 NOT experiment."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Self

from glassmachine.core.errors import ConfigurationError, ReplayMismatchError
from glassmachine.core.logic import LogicValue, LogicVector
from glassmachine.models.digital.not_gate import build_not_simulation
from glassmachine.simulation.engine import Snapshot
from glassmachine.trace.trace import Trace

EXPERIMENT_SCHEMA = "glassmachine.experiment"
EXPERIMENT_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class InputStep:
    time: int
    value: LogicValue

    def __post_init__(self) -> None:
        if self.time < 0:
            raise ConfigurationError("input step time cannot be negative")


@dataclass(frozen=True, slots=True)
class NotExperimentResult:
    output: LogicVector
    trace: Trace
    snapshot: Snapshot


@dataclass(frozen=True, slots=True)
class NotExperiment:
    steps: tuple[InputStep, ...]
    delay: int = 1

    def __post_init__(self) -> None:
        if self.delay < 0:
            raise ConfigurationError("NOT delay cannot be negative")
        times = [step.time for step in self.steps]
        if times != sorted(times):
            raise ConfigurationError("input steps must be ordered by time")

    def run(self) -> NotExperimentResult:
        simulation = build_not_simulation(delay=self.delay)
        base_time = simulation.time
        simulation.trace.clear()
        for index, step in enumerate(self.steps):
            simulation.set_input(
                "input",
                step.value,
                at_time=base_time + step.time,
                reason=f"experiment step {index}",
            )
        simulation.run_until_stable()
        return NotExperimentResult(
            output=simulation.read("output"),
            trace=simulation.trace,
            snapshot=simulation.snapshot(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "delay": self.delay,
            "steps": [{"time": step.time, "value": step.value.value} for step in self.steps],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            delay=int(data["delay"]),
            steps=tuple(
                InputStep(time=int(step["time"]), value=LogicValue.parse(str(step["value"])))
                for step in data["steps"]
            ),
        )


@dataclass(frozen=True, slots=True)
class ExperimentRecord:
    experiment: NotExperiment
    expected_trace_digest: str
    expected_output: str

    @classmethod
    def capture(cls, experiment: NotExperiment) -> Self:
        result = experiment.run()
        return cls(
            experiment=experiment,
            expected_trace_digest=result.trace.digest(),
            expected_output=str(result.output),
        )

    def replay(self) -> NotExperimentResult:
        result = self.experiment.run()
        actual_digest = result.trace.digest()
        if actual_digest != self.expected_trace_digest:
            raise ReplayMismatchError(
                "replayed trace digest differs: "
                f"expected {self.expected_trace_digest}, got {actual_digest}"
            )
        if str(result.output) != self.expected_output:
            raise ReplayMismatchError(
                f"replayed output differs: expected {self.expected_output}, got {result.output}"
            )
        return result

    def write_json(self, path: str | Path) -> None:
        payload = {
            "schema": EXPERIMENT_SCHEMA,
            "version": EXPERIMENT_SCHEMA_VERSION,
            "kind": "not",
            "config": self.experiment.to_dict(),
            "expected_trace_digest": self.expected_trace_digest,
            "expected_output": self.expected_output,
        }
        Path(path).write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    @classmethod
    def read_json(cls, path: str | Path) -> Self:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if (
            payload.get("schema") != EXPERIMENT_SCHEMA
            or payload.get("version") != EXPERIMENT_SCHEMA_VERSION
            or payload.get("kind") != "not"
        ):
            raise ReplayMismatchError("unsupported experiment record")
        return cls(
            experiment=NotExperiment.from_dict(payload["config"]),
            expected_trace_digest=str(payload["expected_trace_digest"]),
            expected_output=str(payload["expected_output"]),
        )
