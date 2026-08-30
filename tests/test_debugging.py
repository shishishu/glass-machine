import unittest

from glassmachine.debugging.debugger import Breakpoint, Debugger
from glassmachine.models.digital.detailed.not_gate import build_not_simulation


class DebuggerTests(unittest.TestCase):
    def test_breaks_on_a_real_output_event(self) -> None:
        simulation = build_not_simulation(delay=1)
        simulation.trace.clear()
        debugger = Debugger(simulation)
        debugger.add_breakpoint(Breakpoint.signal("output"))
        simulation.set_input("input", "0")

        stopped = debugger.run_until_break()
        self.assertIsNotNone(stopped)
        assert stopped is not None
        event, breakpoint = stopped
        self.assertEqual(event.signal, "output")
        self.assertEqual(breakpoint.name, "signal:output")
        self.assertEqual(len(debugger.probe("output")), 1)


if __name__ == "__main__":
    unittest.main()
