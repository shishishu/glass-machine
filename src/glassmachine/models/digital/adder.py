"""Public, immutable result of a one-bit adder evaluation."""

from dataclasses import dataclass

from glassmachine.core.logic import LogicVector


@dataclass(frozen=True, slots=True)
class AdderResult:
    sum: LogicVector
    carry: LogicVector

    def __post_init__(self) -> None:
        self.sum.require_width(1, context="adder sum")
        self.carry.require_width(1, context="adder carry")
