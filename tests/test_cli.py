import io
import unittest
from contextlib import redirect_stdout

from glassmachine.cli import main


class CliTests(unittest.TestCase):
    def test_verify_command(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main(["verify"])
        self.assertEqual(exit_code, 0)
        self.assertIn("M0 NOT validation: PASS", output.getvalue())


if __name__ == "__main__":
    unittest.main()
