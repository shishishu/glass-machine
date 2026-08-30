"""Independent truth-table reference for one-bit NOT semantics."""

from typing import ClassVar

from glassmachine.core.logic import LogicValue, LogicVector


class ReferenceNot:
    """Ground truth copied directly from the published four-state truth table."""

    _TABLE: ClassVar[dict[LogicValue, LogicValue]] = {
        LogicValue.ZERO: LogicValue.ONE,
        LogicValue.ONE: LogicValue.ZERO,
        LogicValue.UNKNOWN: LogicValue.UNKNOWN,
        LogicValue.HIGH_IMPEDANCE: LogicValue.UNKNOWN,
    }

    def evaluate(self, value: LogicVector) -> LogicVector:
        scalar = value.require_width(1, context="ReferenceNot input").scalar
        return LogicVector.bit(self._TABLE[scalar])
