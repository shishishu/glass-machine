"""Explicit four-state digital values.

Vectors are stored most-significant bit first so their string form is stable and
human-readable.  Digital logic deliberately does not coerce Python truth values.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from glassmachine.core.errors import ConfigurationError


class LogicValue(StrEnum):
    """One four-state digital logic value."""

    ZERO = "0"
    ONE = "1"
    UNKNOWN = "X"
    HIGH_IMPEDANCE = "Z"

    @classmethod
    def parse(cls, value: str | LogicValue) -> LogicValue:
        if isinstance(value, LogicValue):
            return value
        try:
            return cls(value.upper())
        except ValueError as exc:
            raise ConfigurationError(f"invalid logic value: {value!r}") from exc


@dataclass(frozen=True, slots=True)
class LogicVector:
    """An immutable, explicitly sized vector of four-state bits."""

    bits: tuple[LogicValue, ...]

    def __post_init__(self) -> None:
        if not self.bits:
            raise ConfigurationError("logic vectors must contain at least one bit")
        if not all(isinstance(bit, LogicValue) for bit in self.bits):
            raise ConfigurationError("logic vector bits must be LogicValue members")

    @classmethod
    def parse(cls, value: str | LogicValue | LogicVector) -> LogicVector:
        if isinstance(value, LogicVector):
            return value
        if isinstance(value, LogicValue):
            return cls((value,))
        normalized = value.strip().replace("_", "").upper()
        if not normalized:
            raise ConfigurationError("logic vector text cannot be empty")
        return cls(tuple(LogicValue.parse(character) for character in normalized))

    @classmethod
    def filled(cls, width: int, value: str | LogicValue) -> LogicVector:
        if width <= 0:
            raise ConfigurationError(f"logic width must be positive, got {width}")
        bit = LogicValue.parse(value)
        return cls((bit,) * width)

    @classmethod
    def bit(cls, value: str | LogicValue) -> LogicVector:
        return cls((LogicValue.parse(value),))

    @property
    def width(self) -> int:
        return len(self.bits)

    @property
    def scalar(self) -> LogicValue:
        if self.width != 1:
            raise ConfigurationError(f"expected a scalar, got {self.width} bits")
        return self.bits[0]

    def require_width(self, expected: int, *, context: str = "value") -> LogicVector:
        if self.width != expected:
            raise ConfigurationError(
                f"{context} requires width {expected}, got {self.width} ({self})"
            )
        return self

    def __str__(self) -> str:
        return "".join(bit.value for bit in self.bits)
