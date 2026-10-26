"""Independent explicit truth tables for the two-input primitives."""

from typing import ClassVar

from glassmachine.core.logic import LogicVector


class ReferenceBinaryGate:
    table: ClassVar[str]

    def evaluate(self, a: LogicVector, b: LogicVector) -> LogicVector:
        left = "01XZ".index(str(a.require_width(1, context="reference gate A")))
        right = "01XZ".index(str(b.require_width(1, context="reference gate B")))
        return LogicVector.bit(self.table[4 * left + right])


class ReferenceAnd(ReferenceBinaryGate):
    table = "000001XX0XXX0XXX"


class ReferenceOr(ReferenceBinaryGate):
    table = "01XX1111X1XXX1XX"


class ReferenceXor(ReferenceBinaryGate):
    table = "01XX10XXXXXXXXXX"
