"""Primitive behavior using independent sets of possible binary values."""

from itertools import product
from typing import ClassVar

from glassmachine.core.logic import LogicVector


class FastBinaryGate:
    operation: ClassVar[str]

    def evaluate(self, a: LogicVector, b: LogicVector) -> LogicVector:
        left = str(a.require_width(1, context="fast gate A"))
        right = str(b.require_width(1, context="fast gate B"))
        xs = (int(left),) if left in "01" else (0, 1)
        ys = (int(right),) if right in "01" else (0, 1)
        results = set()
        for x, y in product(xs, ys):
            if self.operation == "and":
                results.add(x & y)
            elif self.operation == "or":
                results.add(x | y)
            else:
                results.add(x ^ y)
        return LogicVector.bit(str(next(iter(results))) if len(results) == 1 else "X")


class FastAnd(FastBinaryGate):
    operation = "and"


class FastOr(FastBinaryGate):
    operation = "or"


class FastXor(FastBinaryGate):
    operation = "xor"
