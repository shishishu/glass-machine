import tempfile
import unittest
from pathlib import Path

from glassmachine.core.logic import LogicValue
from glassmachine.experiments.not_gate import ExperimentRecord, InputStep, NotExperiment


class ExperimentTests(unittest.TestCase):
    def _experiment(self) -> NotExperiment:
        return NotExperiment(
            delay=1,
            steps=(
                InputStep(0, LogicValue.ZERO),
                InputStep(2, LogicValue.ONE),
                InputStep(4, LogicValue.UNKNOWN),
                InputStep(6, LogicValue.HIGH_IMPEDANCE),
            ),
        )

    def test_record_replays_by_recomputation(self) -> None:
        record = ExperimentRecord.capture(self._experiment())
        result = record.replay()
        self.assertEqual(str(result.output), "X")
        self.assertEqual(result.trace.digest(), record.expected_trace_digest)

    def test_record_file_round_trip(self) -> None:
        record = ExperimentRecord.capture(self._experiment())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "experiment.json"
            record.write_json(path)
            loaded = ExperimentRecord.read_json(path)
        self.assertEqual(record, loaded)
        loaded.replay()


if __name__ == "__main__":
    unittest.main()
