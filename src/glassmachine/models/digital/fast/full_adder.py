"""Direct adder behavior without gates, signal state or event scheduling."""

from glassmachine.core.logic import LogicVector
from glassmachine.models.digital.adder import AdderResult


class FastFullAdder:
    def evaluate(self, a: LogicVector, b: LogicVector, cin: LogicVector) -> AdderResult:
        left = str(a.require_width(1, context="fast adder A"))
        right = str(b.require_width(1, context="fast adder B"))
        carry_in = str(cin.require_width(1, context="fast adder Cin"))
        if all(bit in "01" for bit in (left, right, carry_in)):
            x, y, z = int(left), int(right), int(carry_in)
            return AdderResult(
                LogicVector.bit(str(x ^ y ^ z)),
                LogicVector.bit(str((x & y) | (x & z) | (y & z))),
            )
        # Stable four-state behavior of the specified five-gate network.
        # Do not use binary majority simplification for reconvergent unknowns.
        if left == right == "1":
            carry = "1"
        elif left == right == "0" or (carry_in == "0" and "0" in (left, right)):
            carry = "0"
        else:
            carry = "X"
        return AdderResult(LogicVector.bit("X"), LogicVector.bit(carry))


class FastHalfAdder:
    def evaluate(self, a: LogicVector, b: LogicVector) -> AdderResult:
        left = str(a.require_width(1, context="fast half adder A"))
        right = str(b.require_width(1, context="fast half adder B"))
        sum_bit = str(int(left) ^ int(right)) if left in "01" and right in "01" else "X"
        carry = "0" if "0" in (left, right) else "1" if left == right == "1" else "X"
        return AdderResult(LogicVector.bit(sum_bit), LogicVector.bit(carry))
