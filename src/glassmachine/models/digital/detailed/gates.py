"""Two-input four-state primitives executed by the event kernel."""

from collections.abc import Mapping

from glassmachine.core.component import Component, Port, PortDirection
from glassmachine.core.errors import ConfigurationError, SimulationError
from glassmachine.core.logic import LogicValue, LogicVector


class BinaryGate(Component):
    def __init__(
        self, component_id: str, *, input_a: str, input_b: str,
        output_signal: str, delay: int = 1,
    ) -> None:
        if type(delay) is not int or delay < 0:
            raise ConfigurationError("gate delay must be a nonnegative integer")
        super().__init__(
            component_id,
            ports=(Port("a", PortDirection.INPUT, 1), Port("b", PortDirection.INPUT, 1),
                   Port("out", PortDirection.OUTPUT, 1)),
            bindings={"a": input_a, "b": input_b, "out": output_signal},
            delay=delay,
        )

    def evaluate(self, inputs: Mapping[str, LogicVector]) -> Mapping[str, LogicVector]:
        try:
            a = inputs["a"].require_width(1, context=f"{self.component_id}.a").scalar
            b = inputs["b"].require_width(1, context=f"{self.component_id}.b").scalar
        except KeyError as exc:
            raise SimulationError(f"{self.component_id!r} requires ports 'a' and 'b'") from exc
        return {"out": LogicVector.bit(self._evaluate_bits(a, b))}

    def _evaluate_bits(self, a: LogicValue, b: LogicValue) -> LogicValue:
        raise NotImplementedError


class AndGate(BinaryGate):
    def _evaluate_bits(self, a: LogicValue, b: LogicValue) -> LogicValue:
        if a is LogicValue.ZERO or b is LogicValue.ZERO:
            return LogicValue.ZERO
        if a is LogicValue.ONE and b is LogicValue.ONE:
            return LogicValue.ONE
        return LogicValue.UNKNOWN


class OrGate(BinaryGate):
    def _evaluate_bits(self, a: LogicValue, b: LogicValue) -> LogicValue:
        if a is LogicValue.ONE or b is LogicValue.ONE:
            return LogicValue.ONE
        if a is LogicValue.ZERO and b is LogicValue.ZERO:
            return LogicValue.ZERO
        return LogicValue.UNKNOWN


class XorGate(BinaryGate):
    def _evaluate_bits(self, a: LogicValue, b: LogicValue) -> LogicValue:
        if a not in (LogicValue.ZERO, LogicValue.ONE) or b not in (LogicValue.ZERO, LogicValue.ONE):
            return LogicValue.UNKNOWN
        return LogicValue.ZERO if a is b else LogicValue.ONE
