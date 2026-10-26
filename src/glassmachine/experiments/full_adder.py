"""Versioned full-adder experiments preserve interactive scheduling order."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Self

from glassmachine.core.errors import ConfigurationError, ReplayMismatchError
from glassmachine.core.logic import LogicValue
from glassmachine.models.digital.detailed.full_adder import build_full_adder_simulation
from glassmachine.simulation.engine import Simulation
from glassmachine.trace.events import TraceEvent
from glassmachine.trace.trace import Trace


@dataclass(frozen=True, slots=True)
class AdderInput:
    time: int
    signal: str
    value: LogicValue

    def __post_init__(self) -> None:
        if type(self.time) is not int or self.time < 0:
            raise ConfigurationError("input time must be a nonnegative integer")
        if self.signal not in ("A", "B", "Cin"):
            raise ConfigurationError("adder input must be A, B or Cin")
        if not isinstance(self.value, LogicValue):
            raise ConfigurationError("input value must be a LogicValue")


@dataclass(frozen=True, slots=True)
class AdderAdvance:
    mode: Literal["step", "run"]

    def __post_init__(self) -> None:
        if self.mode not in ("step", "run"):
            raise ConfigurationError("advance mode must be step or run")


AdderAction = AdderInput | AdderAdvance


def apply_action(simulation: Simulation, action: AdderAction, base: int, index: int) -> None:
    if isinstance(action, AdderInput):
        simulation.set_input(
            action.signal,
            action.value,
            at_time=base + action.time,
            reason=f"experiment action {index}",
        )
    elif action.mode == "step":
        simulation.step()
    else:
        simulation.run_until_stable()


@dataclass(frozen=True, slots=True)
class FullAdderExperiment:
    actions: tuple[AdderAction, ...]
    delay: int = 1

    def __post_init__(self) -> None:
        if type(self.delay) is not int or self.delay < 0:
            raise ConfigurationError("gate delay must be a nonnegative integer")
        if not all(isinstance(action, (AdderInput, AdderAdvance)) for action in self.actions):
            raise ConfigurationError("unsupported adder action")

    def run(self) -> Simulation:
        simulation = build_full_adder_simulation(delay=self.delay)
        base = simulation.time
        simulation.trace.clear()
        for index, action in enumerate(self.actions):
            apply_action(simulation, action, base, index)
        simulation.run_until_stable()
        return simulation

    def to_dict(self) -> dict[str, Any]:
        return {
            "delay": self.delay,
            "actions": [
                {"kind": "input", "time": a.time, "signal": a.signal, "value": a.value.value}
                if isinstance(a, AdderInput)
                else {"kind": a.mode}
                for a in self.actions
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        if set(data) != {"delay", "actions"} or not isinstance(data["actions"], list):
            raise ConfigurationError("invalid full-adder config")
        actions: list[AdderAction] = []
        for item in data["actions"]:
            if not isinstance(item, dict):
                raise ConfigurationError("invalid action")
            if item.get("kind") == "input" and set(item) == {"kind", "time", "signal", "value"}:
                if not isinstance(item["value"], str):
                    raise ConfigurationError("invalid input value")
                actions.append(
                    AdderInput(item["time"], item["signal"], LogicValue.parse(item["value"]))
                )
            elif set(item) == {"kind"} and item["kind"] in ("step", "run"):
                actions.append(AdderAdvance(item["kind"]))
            else:
                raise ConfigurationError("unsupported action")
        return cls(tuple(actions), data["delay"])


@dataclass(frozen=True, slots=True)
class FullAdderRecord:
    experiment: FullAdderExperiment
    expected_events: tuple[TraceEvent, ...]
    expected_sum: str
    expected_carry: str

    @classmethod
    def capture(cls, experiment: FullAdderExperiment) -> Self:
        simulation = experiment.run()
        return cls(
            experiment,
            simulation.trace.events,
            str(simulation.read("Sum")),
            str(simulation.read("Cout")),
        )

    def replay(self) -> Simulation:
        simulation = self.experiment.run()
        Trace(self.expected_events).assert_equivalent(simulation.trace)
        if (str(simulation.read("Sum")), str(simulation.read("Cout"))) != (
            self.expected_sum,
            self.expected_carry,
        ):
            raise ReplayMismatchError("full-adder output differs from recorded output")
        return simulation

    def write_json(self, path: str | Path) -> None:
        payload = {
            "schema": "glassmachine.experiment",
            "version": 1,
            "kind": "full-adder",
            "config": self.experiment.to_dict(),
            "expected_events": [event.to_dict() for event in self.expected_events],
            "expected_sum": self.expected_sum,
            "expected_carry": self.expected_carry,
        }
        Path(path).write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    @classmethod
    def read_json(cls, path: str | Path) -> Self:
        try:
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
            if (
                not isinstance(payload, dict)
                or set(payload)
                != {
                    "schema",
                    "version",
                    "kind",
                    "config",
                    "expected_events",
                    "expected_sum",
                    "expected_carry",
                }
                or payload["schema"] != "glassmachine.experiment"
                or type(payload["version"]) is not int
                or payload["version"] != 1
                or payload["kind"] != "full-adder"
            ):
                raise ReplayMismatchError("unsupported full-adder record")
            if not isinstance(payload["config"], dict) or not isinstance(
                payload["expected_events"], list
            ):
                raise ReplayMismatchError("invalid full-adder record")
            for key in ("expected_sum", "expected_carry"):
                if payload[key] not in ("0", "1", "X"):
                    raise ReplayMismatchError("invalid recorded adder output")
            events_list = []
            for item in payload["expected_events"]:
                fields = {
                    "record",
                    "event_id",
                    "time",
                    "delta",
                    "sequence",
                    "kind",
                    "signal",
                    "width",
                    "old_value",
                    "new_value",
                    "source_component",
                    "source_port",
                    "caused_by",
                    "reason",
                }
                if not isinstance(item, dict) or set(item) != fields or item["record"] != "event":
                    raise ReplayMismatchError("invalid recorded event fields")
                for key in ("event_id", "time", "delta", "sequence", "width"):
                    if type(item[key]) is not int or item[key] < 0:
                        raise ReplayMismatchError(f"invalid recorded event {key}")
                if item["width"] != 1:
                    raise ReplayMismatchError("recorded adder event must have width 1")
                if item["caused_by"] is not None and (
                    type(item["caused_by"]) is not int or item["caused_by"] < 0
                ):
                    raise ReplayMismatchError("invalid recorded cause")
                for key in ("kind", "signal", "source_component", "source_port", "reason"):
                    if not isinstance(item[key], str):
                        raise ReplayMismatchError(f"invalid recorded event {key}")
                for key in ("old_value", "new_value"):
                    if item[key] not in ("0", "1", "X", "Z"):
                        raise ReplayMismatchError("invalid recorded scalar value")
                events_list.append(TraceEvent.from_dict(item))
            events = tuple(events_list)
            return cls(
                FullAdderExperiment.from_dict(payload["config"]),
                events,
                payload["expected_sum"],
                payload["expected_carry"],
            )
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            raise ReplayMismatchError(f"invalid full-adder record: {exc}") from exc
