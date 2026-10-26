"""Exhaustive primitives, arithmetic boundary and explicit unknown cases."""

from itertools import product

import pytest

from glassmachine.core.errors import ConfigurationError, SimulationError
from glassmachine.core.logic import LogicVector
from glassmachine.models.digital.adder import AdderResult
from glassmachine.models.digital.detailed.full_adder import (
    build_full_adder_simulation,
    build_half_adder_simulation,
)
from glassmachine.models.digital.detailed.gates import AndGate, OrGate, XorGate
from glassmachine.models.digital.fast.full_adder import FastFullAdder, FastHalfAdder
from glassmachine.models.digital.fast.gates import FastAnd, FastOr, FastXor
from glassmachine.models.digital.reference.full_adder import ReferenceFullAdder, ReferenceHalfAdder
from glassmachine.models.digital.reference.gates import ReferenceAnd, ReferenceOr, ReferenceXor


@pytest.mark.parametrize(
    "detailed,reference,fast,rows",
    [
        (AndGate, ReferenceAnd, FastAnd, ("0000", "01XX", "0XXX", "0XXX")),
        (OrGate, ReferenceOr, FastOr, ("01XX", "1111", "X1XX", "X1XX")),
        (XorGate, ReferenceXor, FastXor, ("01XX", "10XX", "XXXX", "XXXX")),
    ],
)
def test_gate_truth_tables(detailed, reference, fast, rows) -> None:
    gate = detailed("gate", input_a="a", input_b="b", output_signal="out")
    for i, a in enumerate("01XZ"):
        for j, b in enumerate("01XZ"):
            av, bv = LogicVector.bit(a), LogicVector.bit(b)
            expected = LogicVector.bit(rows[i][j])
            assert reference().evaluate(av, bv) == expected
            assert fast().evaluate(av, bv) == expected
            assert gate.evaluate({"a": av, "b": bv})["out"] == expected


@pytest.mark.parametrize("delay", [0, 1, 3])
def test_all_full_adder_inputs(delay: int) -> None:
    for bits in product("01XZ", repeat=3):
        values = tuple(LogicVector.bit(bit) for bit in bits)
        reference = ReferenceFullAdder().evaluate(*values)
        assert FastFullAdder().evaluate(*values) == reference
        simulation = build_full_adder_simulation(delay=delay)
        for name, bit in zip(("A", "B", "Cin"), bits, strict=True):
            simulation.set_input(name, bit)
        simulation.run_until_stable()
        assert AdderResult(simulation.read("Sum"), simulation.read("Cout")) == reference
        if all(bit in "01" for bit in bits):
            total = sum(int(bit) for bit in bits)
            assert str(reference.sum) == str(total % 2)
            assert str(reference.carry) == str(total // 2)


def test_all_half_adder_inputs() -> None:
    for bits in product("01XZ", repeat=2):
        values = tuple(LogicVector.bit(bit) for bit in bits)
        reference = ReferenceHalfAdder().evaluate(*values)
        assert FastHalfAdder().evaluate(*values) == reference
        simulation = build_half_adder_simulation()
        for name, bit in zip(("A", "B"), bits, strict=True):
            simulation.set_input(name, bit)
        simulation.run_until_stable()
        assert AdderResult(simulation.read("Sum"), simulation.read("Cout")) == reference


@pytest.mark.parametrize("bits,expected", [("1X1", "XX"), ("11X", "X1"), ("0Z0", "X0")])
def test_structural_unknown_contract(bits: str, expected: str) -> None:
    for model in (ReferenceFullAdder(), FastFullAdder()):
        result = model.evaluate(*(LogicVector.bit(bit) for bit in bits))
        assert str(result.sum) + str(result.carry) == expected


def test_invalid_width_ports_and_delay() -> None:
    wide, bit = LogicVector.parse("00"), LogicVector.bit("0")
    for model in (ReferenceFullAdder(), FastFullAdder()):
        for values in ((wide, bit, bit), (bit, wide, bit), (bit, bit, wide)):
            with pytest.raises(ConfigurationError):
                model.evaluate(*values)
    for model in (ReferenceHalfAdder(), FastHalfAdder(), ReferenceAnd(), FastAnd()):
        with pytest.raises(ConfigurationError):
            model.evaluate(wide, bit)
    gate = AndGate("gate", input_a="a", input_b="b", output_signal="out")
    with pytest.raises(SimulationError):
        gate.evaluate({"a": bit})
    with pytest.raises(ConfigurationError):
        gate.evaluate({"a": bit, "b": wide})
    with pytest.raises(ConfigurationError):
        build_full_adder_simulation(delay=-1)
    with pytest.raises(ConfigurationError):
        AdderResult(wide, bit)


@pytest.mark.parametrize("delay", [-1, 0.5, True, False, "1", None])
def test_gate_and_builder_reject_invalid_delay(delay) -> None:
    for builder in (build_full_adder_simulation, build_half_adder_simulation):
        with pytest.raises(ConfigurationError, match="nonnegative integer"):
            builder(delay=delay)
    for gate_type in (AndGate, OrGate, XorGate):
        with pytest.raises(ConfigurationError, match="nonnegative integer"):
            gate_type("gate", input_a="a", input_b="b", output_signal="out", delay=delay)
