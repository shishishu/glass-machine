"""Integer reference for binary inputs and explicit structural four-state oracle."""

from types import MappingProxyType

from glassmachine.core.logic import LogicVector
from glassmachine.models.digital.adder import AdderResult

# Rows encode (Sum, Cout), indexed by A+B+Cin after Z→X normalization.
# This fixed five-gate contract deliberately retains reconvergent X pessimism.
_FULL_TABLE = MappingProxyType({
    "000": "00", "001": "10", "00X": "X0",
    "010": "10", "011": "01", "01X": "XX",
    "0X0": "X0", "0X1": "XX", "0XX": "XX",
    "100": "10", "101": "01", "10X": "XX",
    "110": "01", "111": "11", "11X": "X1",
    "1X0": "XX", "1X1": "XX", "1XX": "XX",
    "X00": "X0", "X01": "XX", "X0X": "XX",
    "X10": "XX", "X11": "XX", "X1X": "XX",
    "XX0": "XX", "XX1": "XX", "XXX": "XX",
})
_HALF_TABLE = MappingProxyType({
    "00": "00", "01": "10", "0X": "X0",
    "10": "10", "11": "01", "1X": "XX",
    "X0": "X0", "X1": "XX", "XX": "XX",
})


def _key(*values: LogicVector) -> str:
    return "".join(str(value.require_width(1, context="reference adder input"))
                   for value in values).replace("Z", "X")


def _result(key: str, table: MappingProxyType[str, str]) -> AdderResult:
    if "X" not in key:
        total = sum(int(bit) for bit in key)
        return AdderResult(LogicVector.bit(str(total % 2)), LogicVector.bit(str(total // 2)))
    result = table[key]
    return AdderResult(LogicVector.bit(result[0]), LogicVector.bit(result[1]))


class ReferenceFullAdder:
    def evaluate(self, a: LogicVector, b: LogicVector, cin: LogicVector) -> AdderResult:
        return _result(_key(a, b, cin), _FULL_TABLE)


class ReferenceHalfAdder:
    def evaluate(self, a: LogicVector, b: LogicVector) -> AdderResult:
        return _result(_key(a, b), _HALF_TABLE)
