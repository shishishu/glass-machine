"""Independent literal expectations, rather than agreement alone."""

from itertools import product

import pytest

from glassmachine.core.errors import ConfigurationError, ValidationError
from glassmachine.core.logic import LogicValue, LogicVector
from glassmachine.models.digital.detailed.full_adder import build_half_adder_simulation
from glassmachine.models.digital.fast.full_adder import FastFullAdder, FastHalfAdder
from glassmachine.models.digital.reference.full_adder import ReferenceFullAdder, ReferenceHalfAdder
from glassmachine.validation.full_adder import (
    FullAdderValidationReport,
    validate_full_adder_models,
)

# Rows indexed by A/B; columns Cin=0,1,X. Each literal is Sum then Cout.
# This is the five-gate contract, deliberately not ideal ternary arithmetic.
FULL_CASES = {
    "00": ("00", "10", "X0"),
    "01": ("10", "01", "XX"),
    "0X": ("X0", "XX", "XX"),
    "10": ("10", "01", "XX"),
    "11": ("01", "11", "X1"),
    "1X": ("XX", "XX", "XX"),
    "X0": ("X0", "XX", "XX"),
    "X1": ("XX", "XX", "XX"),
    "XX": ("XX", "XX", "XX"),
}
HALF_CASES = {
    "00": "00", "01": "10", "0X": "X0",
    "10": "10", "11": "01", "1X": "XX",
    "X0": "X0", "X1": "XX", "XX": "XX",
}


def test_all_64_cases_match_literal_structural_specification() -> None:
    report = validate_full_adder_models()
    assert report.passed
    assert len(report.rows) == 64
    assert {(r.a, r.b, r.cin) for r in report.rows} == set(product(LogicValue, repeat=3))
    for row in report.rows:
        a, b, cin = (str(v).replace("Z", "X") for v in (row.a, row.b, row.cin))
        expected = FULL_CASES[a + b]["01X".index(cin)]
        for result in (row.reference, row.fast, row.detailed):
            assert str(result.sum) + str(result.carry) == expected, (row, expected)
        if all(v in "01" for v in (a, b, cin)):
            total = int(a) + int(b) + int(cin)
            assert expected == f"{total % 2}{total // 2}"


def test_unknown_structural_carry_is_not_ideal_arithmetic() -> None:
    # Both arithmetic possibilities total 2 or 3 (carry 1), but the fixed
    # reconvergent gate graph loses correlation and correctly returns X.
    for model in (ReferenceFullAdder(), FastFullAdder()):
        result = model.evaluate(*(LogicVector.bit(v) for v in "1X1"))
        assert str(result.sum) == str(result.carry) == "X"


@pytest.mark.parametrize("a,b", list(product("01XZ", repeat=2)))
def test_half_adder_literal_table(a: str, b: str) -> None:
    expected = HALF_CASES[(a + b).replace("Z", "X")]
    for model in (ReferenceHalfAdder(), FastHalfAdder()):
        result = model.evaluate(LogicVector.bit(a), LogicVector.bit(b))
        assert str(result.sum) + str(result.carry) == expected
    simulation = build_half_adder_simulation()
    simulation.set_input("A", a)
    simulation.set_input("B", b)
    simulation.run_until_stable()
    assert str(simulation.read("Sum")) + str(simulation.read("Cout")) == expected


@pytest.mark.parametrize("model", [ReferenceFullAdder(), FastFullAdder()])
@pytest.mark.parametrize("position", range(3))
def test_full_adder_rejects_non_scalar_ports(model, position: int) -> None:
    values = [LogicVector.bit("0") for _ in range(3)]
    values[position] = LogicVector.parse("00")
    with pytest.raises(ConfigurationError):
        model.evaluate(*values)


def test_empty_report_is_not_success() -> None:
    report = FullAdderValidationReport(())
    assert not report.passed
    with pytest.raises(ValidationError, match="no cases"):
        report.require_passed()
