"""Component and port contracts used by the deterministic simulation engine."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType

from glassmachine.core.errors import ConfigurationError
from glassmachine.core.logic import LogicVector


class PortDirection(StrEnum):
    INPUT = "input"
    OUTPUT = "output"


@dataclass(frozen=True, slots=True)
class Port:
    name: str
    direction: PortDirection
    width: int

    def __post_init__(self) -> None:
        if not self.name:
            raise ConfigurationError("port name cannot be empty")
        if self.width <= 0:
            raise ConfigurationError(f"port {self.name!r} must have positive width")


class Component(ABC):
    """A deterministic combinational component.

    Sequential state will extend this contract in M1.  M0 intentionally keeps
    the component surface small enough to audit.
    """

    def __init__(
        self,
        component_id: str,
        *,
        ports: tuple[Port, ...],
        bindings: Mapping[str, str],
        delay: int = 0,
    ) -> None:
        if not component_id:
            raise ConfigurationError("component ID cannot be empty")
        if delay < 0:
            raise ConfigurationError("component delay cannot be negative")
        names = [port.name for port in ports]
        if len(names) != len(set(names)):
            raise ConfigurationError(f"component {component_id!r} has duplicate port names")
        if set(bindings) != set(names):
            raise ConfigurationError(
                f"component {component_id!r} bindings must exactly match its ports"
            )
        self._component_id = component_id
        self._ports = ports
        self._bindings = MappingProxyType(dict(bindings))
        self._delay = delay

    @property
    def component_id(self) -> str:
        return self._component_id

    @property
    def ports(self) -> tuple[Port, ...]:
        return self._ports

    @property
    def bindings(self) -> Mapping[str, str]:
        return self._bindings

    @property
    def delay(self) -> int:
        return self._delay

    @abstractmethod
    def evaluate(self, inputs: Mapping[str, LogicVector]) -> Mapping[str, LogicVector]:
        """Return every output value for the supplied immutable input snapshot."""
