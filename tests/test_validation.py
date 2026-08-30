import unittest

from glassmachine.core.logic import LogicValue, LogicVector
from glassmachine.models.digital.fast.not_gate import FastNot
from glassmachine.models.digital.reference.not_gate import ReferenceNot
from glassmachine.validation.not_gate import validate_not_models


class ValidationTests(unittest.TestCase):
    def test_literal_not_truth_table(self) -> None:
        literal_cases = (
            ("0", "1"),
            ("1", "0"),
            ("X", "X"),
            ("Z", "X"),
        )
        reference = ReferenceNot()
        fast = FastNot()
        for input_text, expected_text in literal_cases:
            value = LogicVector.parse(input_text)
            expected = LogicVector.parse(expected_text)
            self.assertEqual(reference.evaluate(value), expected)
            self.assertEqual(fast.evaluate(value), expected)

    def test_all_models_agree_exhaustively(self) -> None:
        report = validate_not_models()
        self.assertTrue(report.passed)
        self.assertEqual(
            {row.input_value for row in report.rows},
            set(LogicValue),
        )


if __name__ == "__main__":
    unittest.main()
