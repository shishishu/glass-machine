"""Auditable events emitted only after a state change is committed."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Self

from glassmachine.core.logic import LogicVector


class EventKind(StrEnum):
    INPUT_CHANGED = "input_changed"
    SIGNAL_CHANGED = "signal_changed"


@dataclass(frozen=True, slots=True)
class TraceEvent:
    event_id: int
    time: int
    delta: int
    sequence: int
    kind: EventKind
    signal: str
    width: int
    old_value: LogicVector
    new_value: LogicVector
    source_component: str
    source_port: str
    caused_by: int | None
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "record": "event",
            "event_id": self.event_id,
            "time": self.time,
            "delta": self.delta,
            "sequence": self.sequence,
            "kind": self.kind.value,
            "signal": self.signal,
            "width": self.width,
            "old_value": str(self.old_value),
            "new_value": str(self.new_value),
            "source_component": self.source_component,
            "source_port": self.source_port,
            "caused_by": self.caused_by,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            event_id=int(data["event_id"]),
            time=int(data["time"]),
            delta=int(data["delta"]),
            sequence=int(data["sequence"]),
            kind=EventKind(str(data["kind"])),
            signal=str(data["signal"]),
            width=int(data["width"]),
            old_value=LogicVector.parse(str(data["old_value"])),
            new_value=LogicVector.parse(str(data["new_value"])),
            source_component=str(data["source_component"]),
            source_port=str(data["source_port"]),
            caused_by=None if data.get("caused_by") is None else int(data["caused_by"]),
            reason=str(data["reason"]),
        )
