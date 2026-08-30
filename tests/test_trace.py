import tempfile
import unittest
from pathlib import Path

from glassmachine.core.errors import ReplayMismatchError
from glassmachine.models.digital.detailed.not_gate import build_not_simulation
from glassmachine.trace.trace import Trace


class TraceTests(unittest.TestCase):
    def _trace(self) -> Trace:
        simulation = build_not_simulation()
        simulation.trace.clear()
        simulation.set_input("input", "0")
        simulation.run_until_stable()
        return simulation.trace

    def test_jsonl_round_trip_is_exact(self) -> None:
        trace = self._trace()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace.jsonl"
            trace.write_jsonl(path)
            loaded = Trace.read_jsonl(path)
        trace.assert_equivalent(loaded)
        self.assertEqual(trace.digest(), loaded.digest())

    def test_mismatch_reports_first_event(self) -> None:
        trace = self._trace()
        with self.assertRaises(ReplayMismatchError):
            trace.assert_equivalent(Trace())


if __name__ == "__main__":
    unittest.main()
