import unittest

from glassmachine.core.errors import ConfigurationError
from glassmachine.core.logic import LogicValue, LogicVector


class LogicValueTests(unittest.TestCase):
    def test_parse_is_explicit_and_case_insensitive(self) -> None:
        self.assertIs(LogicValue.parse("x"), LogicValue.UNKNOWN)
        self.assertIs(LogicValue.parse(LogicValue.ONE), LogicValue.ONE)

    def test_invalid_value_fails_loudly(self) -> None:
        with self.assertRaises(ConfigurationError):
            LogicValue.parse("maybe")


class LogicVectorTests(unittest.TestCase):
    def test_vector_preserves_width_and_text(self) -> None:
        vector = LogicVector.parse("10_XZ")
        self.assertEqual(vector.width, 4)
        self.assertEqual(str(vector), "10XZ")

    def test_empty_vector_is_rejected(self) -> None:
        with self.assertRaises(ConfigurationError):
            LogicVector.parse("")

    def test_scalar_rejects_wide_vector(self) -> None:
        with self.assertRaises(ConfigurationError):
            _ = LogicVector.parse("10").scalar

    def test_require_width_is_checked(self) -> None:
        with self.assertRaises(ConfigurationError):
            LogicVector.parse("10").require_width(1)


if __name__ == "__main__":
    unittest.main()
