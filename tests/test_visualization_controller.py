import unittest

from glassmachine.visualization.controller import NotDemoController


class VisualizationControllerTests(unittest.TestCase):
    def test_controller_renders_only_committed_simulation_state(self) -> None:
        controller = NotDemoController(delay=1)
        committed = controller.apply("0")
        state = controller.state

        self.assertEqual(state.input_value, "0")
        self.assertEqual(state.output_value, "1")
        self.assertEqual([event.signal for event in committed], ["input", "output"])
        self.assertEqual(state.trace_digest, controller.simulation.trace.digest())


if __name__ == "__main__":
    unittest.main()
