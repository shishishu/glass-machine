"""Exhaustive comparison of the declared four-state full-adder models."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product

from glassmachine.core.errors import ValidationError
from glassmachine.core.logic import LogicValue, LogicVector
from glassmachine.models.digital.adder import AdderResult
from glassmachine.models.digital.detailed.full_adder import build_full_adder_simulation
from glassmachine.models.digital.fast.full_adder import FastFullAdder
from glassmachine.models.digital.reference.full_adder import ReferenceFullAdder


@dataclass(frozen=True, slots=True)
class FullAdderValidationRow:
    a: LogicValue
    b: LogicValue
    cin: LogicValue
    reference: AdderResult
    detailed: AdderResult
    fast: AdderResult
    trace_digest: str

    @property
    def passed(self) -> bool:
        return self.reference == self.detailed == self.fast


@dataclass(frozen=True, slots=True)
class FullAdderValidationReport:
    rows: tuple[FullAdderValidationRow, ...]

    @property
    def passed(self) -> bool:
        return bool(self.rows) and all(row.passed for row in self.rows)

    def require_passed(self) -> None:
        if not self.rows:
            raise ValidationError("full-adder validation has no cases")
        for row in self.rows:
            if not row.passed:
                raise ValidationError(f"full-adder models first disagree at {row!r}")


def validate_full_adder_models() -> FullAdderValidationReport:
    reference = ReferenceFullAdder()
    fast = FastFullAdder()
    rows = []
    for a, b, cin in product(LogicValue, repeat=3):
        values = tuple(LogicVector.bit(bit) for bit in (a, b, cin))
        simulation = build_full_adder_simulation()
        simulation.trace.clear()
        for signal, value in zip(("A", "B", "Cin"), values, strict=True):
            simulation.set_input(signal, value, reason="full-adder differential validation")
        simulation.run_until_stable()
        rows.append(
            FullAdderValidationRow(
                a=a,
                b=b,
                cin=cin,
                reference=reference.evaluate(*values),
                detailed=AdderResult(simulation.read("Sum"), simulation.read("Cout")),
                fast=fast.evaluate(*values),
                trace_digest=simulation.trace.digest(),
            )
        )
    report = FullAdderValidationReport(tuple(rows))
    report.require_passed()
    return report
