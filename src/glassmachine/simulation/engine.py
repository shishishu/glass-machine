"""A small deterministic event kernel for the M0 vertical slice."""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Any

from glassmachine.core.component import Component, Port, PortDirection
from glassmachine.core.errors import ConfigurationError, SimulationError, UnstableSimulationError
from glassmachine.core.logic import LogicValue, LogicVector
from glassmachine.trace.events import EventKind, TraceEvent
from glassmachine.trace.trace import Trace


@dataclass(slots=True)
class _SignalState:
    name: str
    width: int
    value: LogicVector
    external: bool
    driver: str | None = None
    subscribers: list[str] = field(default_factory=list)


@dataclass(order=True, frozen=True, slots=True)
class _ScheduledChange:
    time: int
    delta: int
    sequence: int
    event_id: int = field(compare=False)
    kind: EventKind = field(compare=False)
    signal: str = field(compare=False)
    value: LogicVector = field(compare=False)
    source_component: str = field(compare=False)
    source_port: str = field(compare=False)
    caused_by: int | None = field(compare=False)
    reason: str = field(compare=False)


@dataclass(frozen=True, slots=True)
class Snapshot:
    """A stable-state snapshot suitable for deterministic restart."""

    schema_version: int
    time: int
    signal_widths: tuple[tuple[str, int], ...]
    signal_values: tuple[tuple[str, str], ...]


class Simulation:
    """Owns all signal state and is the sole source of committed changes."""

    SNAPSHOT_SCHEMA_VERSION = 1

    def __init__(self) -> None:
        self._signals: dict[str, _SignalState] = {}
        self._components: dict[str, Component] = {}
        self._queue: list[_ScheduledChange] = []
        self._next_sequence = 1
        self._time = 0
        self._delta = 0
        self._initialized = False
        self.trace = Trace()

    @property
    def time(self) -> int:
        return self._time

    @property
    def delta(self) -> int:
        return self._delta

    @property
    def pending_events(self) -> int:
        return len(self._queue)

    def add_signal(
        self,
        name: str,
        *,
        width: int = 1,
        initial: str | LogicValue | LogicVector = LogicValue.HIGH_IMPEDANCE,
        external: bool = False,
    ) -> None:
        self._require_mutable_graph()
        if not name:
            raise ConfigurationError("signal name cannot be empty")
        if name in self._signals:
            raise ConfigurationError(f"duplicate signal: {name!r}")
        if width <= 0:
            raise ConfigurationError(f"signal {name!r} must have positive width")
        value = LogicVector.parse(initial).require_width(width, context=f"signal {name!r}")
        self._signals[name] = _SignalState(
            name=name,
            width=width,
            value=value,
            external=external,
            driver="__external__" if external else None,
        )

    def add_component(self, component: Component) -> None:
        self._require_mutable_graph()
        if component.component_id in self._components:
            raise ConfigurationError(f"duplicate component: {component.component_id!r}")
        resolved_ports: list[tuple[Port, _SignalState]] = []
        for port in component.ports:
            signal_name = component.bindings[port.name]
            try:
                signal = self._signals[signal_name]
            except KeyError as exc:
                raise ConfigurationError(
                    f"component {component.component_id!r} binds unknown signal {signal_name!r}"
                ) from exc
            if signal.width != port.width:
                raise ConfigurationError(
                    f"component {component.component_id!r} port {port.name!r} has width "
                    f"{port.width}, but signal {signal_name!r} has width {signal.width}"
                )
            if port.direction is PortDirection.OUTPUT and signal.driver is not None:
                raise ConfigurationError(
                    f"signal {signal_name!r} already has driver {signal.driver!r}; "
                    f"cannot add {component.component_id!r}"
                )
            resolved_ports.append((port, signal))

        # Mutate the graph only after every binding has passed validation.
        for port, signal in resolved_ports:
            if port.direction is PortDirection.OUTPUT:
                signal.driver = component.component_id
            else:
                signal.subscribers.append(component.component_id)
        self._components[component.component_id] = component

    def initialize(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        for component_id in sorted(self._components):
            self._evaluate_component(
                self._components[component_id], caused_by=None, reason="initialize"
            )

    def set_input(
        self,
        signal: str,
        value: str | LogicValue | LogicVector,
        *,
        at_time: int | None = None,
        reason: str = "external input",
    ) -> int:
        state = self._get_signal(signal)
        if not state.external:
            raise ConfigurationError(f"signal {signal!r} is not an external input")
        parsed = LogicVector.parse(value).require_width(state.width, context=f"input {signal!r}")
        target_time = self._time if at_time is None else at_time
        return self._schedule_change(
            kind=EventKind.INPUT_CHANGED,
            signal=signal,
            value=parsed,
            source_component="__external__",
            source_port=signal,
            caused_by=None,
            reason=reason,
            target_time=target_time,
            delay=0,
        )

    def step(self) -> TraceEvent | None:
        if not self._queue:
            return None
        scheduled = heapq.heappop(self._queue)
        if scheduled.time < self._time:
            raise SimulationError("scheduler attempted to move backwards in time")
        self._time = scheduled.time
        self._delta = scheduled.delta
        signal = self._get_signal(scheduled.signal)
        if signal.value == scheduled.value:
            return None
        old_value = signal.value
        signal.value = scheduled.value
        event = TraceEvent(
            event_id=scheduled.event_id,
            time=scheduled.time,
            delta=scheduled.delta,
            sequence=scheduled.sequence,
            kind=scheduled.kind,
            signal=scheduled.signal,
            width=signal.width,
            old_value=old_value,
            new_value=scheduled.value,
            source_component=scheduled.source_component,
            source_port=scheduled.source_port,
            caused_by=scheduled.caused_by,
            reason=scheduled.reason,
        )
        self.trace.append(event)
        for component_id in sorted(signal.subscribers):
            self._evaluate_component(
                self._components[component_id],
                caused_by=event.event_id,
                reason=f"{scheduled.signal} changed",
            )
        return event

    def run_until_stable(self, *, max_events: int = 10_000) -> tuple[TraceEvent, ...]:
        if max_events <= 0:
            raise ConfigurationError("max_events must be positive")
        committed: list[TraceEvent] = []
        processed = 0
        while self._queue and processed < max_events:
            event = self.step()
            processed += 1
            if event is not None:
                committed.append(event)
        if self._queue:
            raise UnstableSimulationError(
                f"simulation did not settle within {max_events} scheduled events"
            )
        return tuple(committed)

    def read(self, signal: str) -> LogicVector:
        return self._get_signal(signal).value

    def signal_values(self) -> dict[str, LogicVector]:
        return {name: state.value for name, state in sorted(self._signals.items())}

    def snapshot(self) -> Snapshot:
        if self._queue:
            raise SimulationError("snapshots require a stable simulation with no pending events")
        return Snapshot(
            schema_version=self.SNAPSHOT_SCHEMA_VERSION,
            time=self._time,
            signal_widths=tuple(
                (name, state.width) for name, state in sorted(self._signals.items())
            ),
            signal_values=tuple(
                (name, str(state.value)) for name, state in sorted(self._signals.items())
            ),
        )

    def restore(self, snapshot: Snapshot) -> None:
        if self._queue:
            raise SimulationError("cannot restore while events are pending")
        if snapshot.schema_version != self.SNAPSHOT_SCHEMA_VERSION:
            raise ConfigurationError(
                f"unsupported snapshot version: {snapshot.schema_version}"
            )
        widths = tuple((name, state.width) for name, state in sorted(self._signals.items()))
        if widths != snapshot.signal_widths:
            raise ConfigurationError("snapshot signal layout does not match this simulation")
        values = dict(snapshot.signal_values)
        for name, state in self._signals.items():
            state.value = LogicVector.parse(values[name]).require_width(
                state.width, context=f"snapshot signal {name!r}"
            )
        self._time = snapshot.time
        self._delta = 0
        self._next_sequence = 1
        self.trace.clear()

    def _evaluate_component(
        self, component: Component, *, caused_by: int | None, reason: str
    ) -> None:
        inputs = {
            port.name: self._get_signal(component.bindings[port.name]).value
            for port in component.ports
            if port.direction is PortDirection.INPUT
        }
        outputs = dict(component.evaluate(inputs))
        output_ports = {
            port.name: port for port in component.ports if port.direction is PortDirection.OUTPUT
        }
        if set(outputs) != set(output_ports):
            raise SimulationError(
                f"component {component.component_id!r} returned outputs {set(outputs)!r}; "
                f"expected {set(output_ports)!r}"
            )
        for port_name, value in outputs.items():
            port = output_ports[port_name]
            parsed = LogicVector.parse(value).require_width(
                port.width, context=f"component {component.component_id!r}.{port_name}"
            )
            signal_name = component.bindings[port_name]
            if self._get_signal(signal_name).value == parsed:
                continue
            self._schedule_change(
                kind=EventKind.SIGNAL_CHANGED,
                signal=signal_name,
                value=parsed,
                source_component=component.component_id,
                source_port=port_name,
                caused_by=caused_by,
                reason=reason,
                target_time=self._time,
                delay=component.delay,
            )

    def _schedule_change(
        self,
        *,
        kind: EventKind,
        signal: str,
        value: LogicVector,
        source_component: str,
        source_port: str,
        caused_by: int | None,
        reason: str,
        target_time: int,
        delay: int,
    ) -> int:
        if target_time < self._time:
            raise ConfigurationError(
                f"cannot schedule signal {signal!r} in the past: {target_time} < {self._time}"
            )
        if delay < 0:
            raise ConfigurationError("event delay cannot be negative")
        event_time = target_time + delay
        event_delta = self._delta + 1 if event_time == self._time else 0
        sequence = self._next_sequence
        self._next_sequence += 1
        scheduled = _ScheduledChange(
            time=event_time,
            delta=event_delta,
            sequence=sequence,
            event_id=sequence,
            kind=kind,
            signal=signal,
            value=value,
            source_component=source_component,
            source_port=source_port,
            caused_by=caused_by,
            reason=reason,
        )
        heapq.heappush(self._queue, scheduled)
        return scheduled.event_id

    def _get_signal(self, name: str) -> _SignalState:
        try:
            return self._signals[name]
        except KeyError as exc:
            raise ConfigurationError(f"unknown signal: {name!r}") from exc

    def _require_mutable_graph(self) -> None:
        if self._initialized:
            raise ConfigurationError("cannot change the circuit graph after initialization")

    def describe(self) -> dict[str, Any]:
        """Return a stable, JSON-compatible summary for debugging and reports."""

        return {
            "time": self._time,
            "delta": self._delta,
            "pending_events": len(self._queue),
            "signals": {
                name: {"width": state.width, "value": str(state.value)}
                for name, state in sorted(self._signals.items())
            },
            "components": sorted(self._components),
            "trace_digest": self.trace.digest(),
        }
