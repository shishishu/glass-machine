"""Compact behavior model kept independent from ReferenceNot and NotGate."""

from glassmachine.core.logic import LogicVector


class FastNot:
    _TRANSLATION = str.maketrans({"0": "1", "1": "0", "X": "X", "Z": "X"})

    def evaluate(self, value: LogicVector) -> LogicVector:
        value.require_width(1, context="FastNot input")
        return LogicVector.parse(str(value).translate(self._TRANSLATION))
