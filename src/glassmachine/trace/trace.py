"""JSONL persistence and stable digests for execution traces."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any, Self

from glassmachine.core.errors import ReplayMismatchError
from glassmachine.trace.events import TraceEvent

TRACE_SCHEMA = "glassmachine.trace"
TRACE_SCHEMA_VERSION = 1


class Trace:
    def __init__(self, events: Iterable[TraceEvent] = ()) -> None:
        self._events = list(events)

    def append(self, event: TraceEvent) -> None:
        self._events.append(event)

    def clear(self) -> None:
        self._events.clear()

    def __iter__(self) -> Iterator[TraceEvent]:
        return iter(self._events)

    def __len__(self) -> int:
        return len(self._events)

    def __getitem__(self, index: int) -> TraceEvent:
        return self._events[index]

    @property
    def events(self) -> tuple[TraceEvent, ...]:
        return tuple(self._events)

    def for_signal(self, signal: str) -> tuple[TraceEvent, ...]:
        return tuple(event for event in self._events if event.signal == signal)

    def records(self) -> Iterator[dict[str, Any]]:
        yield {
            "record": "header",
            "schema": TRACE_SCHEMA,
            "version": TRACE_SCHEMA_VERSION,
        }
        for event in self._events:
            yield event.to_dict()

    def digest(self) -> str:
        canonical = "\n".join(
            json.dumps(record, sort_keys=True, separators=(",", ":"))
            for record in self.records()
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def write_jsonl(self, path: str | Path) -> None:
        destination = Path(path)
        with destination.open("w", encoding="utf-8") as stream:
            for record in self.records():
                stream.write(json.dumps(record, sort_keys=True))
                stream.write("\n")

    @classmethod
    def read_jsonl(cls, path: str | Path) -> Self:
        source = Path(path)
        with source.open(encoding="utf-8") as stream:
            records = [json.loads(line) for line in stream if line.strip()]
        if not records:
            raise ReplayMismatchError(f"trace is empty: {source}")
        header = records[0]
        if (
            header.get("record") != "header"
            or header.get("schema") != TRACE_SCHEMA
            or header.get("version") != TRACE_SCHEMA_VERSION
        ):
            raise ReplayMismatchError(f"unsupported trace header: {header!r}")
        events = []
        for record in records[1:]:
            if record.get("record") != "event":
                raise ReplayMismatchError(f"unsupported trace record: {record!r}")
            events.append(TraceEvent.from_dict(record))
        return cls(events)

    def assert_equivalent(self, other: Trace) -> None:
        for index, (left, right) in enumerate(zip(self._events, other._events, strict=False)):
            if left != right:
                raise ReplayMismatchError(
                    f"trace diverged at event index {index}: expected {left}, got {right}"
                )
        if len(self) != len(other):
            raise ReplayMismatchError(
                f"trace lengths differ: expected {len(self)}, got {len(other)}"
            )
