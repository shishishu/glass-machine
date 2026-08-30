"""Exhaustive differential validation for the M0 NOT vertical slice."""

from __future__ import annotations

from dataclasses import dataclass

from glassmachine.core.errors import ValidationError
from glassmachine.core.logic import LogicValue, LogicVector
from glassmachine.models.digital.detailed.not_gate import build_not_simulation
from glassmachine.models.digital.fast.not_gate import FastNot
from glassmachine.models.digital.reference.not_gate import ReferenceNot


@dataclass(frozen=True, slots=True)
class NotValidationRow:
    input_value: LogicValue
    reference: LogicVector
    detailed: LogicVector
    fast: LogicVector
    trace_digest: str

    @property
    def passed(self) -> bool:
        return self.reference == self.detailed == self.fast


@dataclass(frozen=True, slots=True)
class NotValidationReport:
    rows: tuple[NotValidationRow, ...]

    @property
    def passed(self) -> bool:
        return all(row.passed for row in self.rows)

    def require_passed(self) -> None:
        failures = [row for row in self.rows if not row.passed]
        if failures:
            raise ValidationError(f"NOT models disagree: {failures!r}")


def validate_not_models() -> NotValidationReport:
    reference = ReferenceNot()
    fast = FastNot()
    rows = []
    for input_value in LogicValue:
        value = LogicVector.bit(input_value)
        simulation = build_not_simulation(delay=1)
        simulation.trace.clear()
        simulation.set_input("input", value, reason="differential validation")
        simulation.run_until_stable()
        rows.append(
            NotValidationRow(
                input_value=input_value,
                reference=reference.evaluate(value),
                detailed=simulation.read("output"),
                fast=fast.evaluate(value),
                trace_digest=simulation.trace.digest(),
            )
        )
    report = NotValidationReport(tuple(rows))
    report.require_passed()
    return report
