"""Run the M1 learning transition without Qt or file side effects."""

from glassmachine.validation.full_adder import validate_full_adder_models
from glassmachine.visualization.full_adder_controller import FullAdderController

controller = FullAdderController(delay=1)
for signal, value in (("A", "0"), ("B", "1"), ("Cin", "1")):
    controller.queue(signal, value)
controller.run()
start = len(controller.simulation.trace)
controller.queue("A", "1")
controller.step()
controller.run()
for event in controller.simulation.trace.events[start:]:
    print(
        f"t={event.time} delta={event.delta} {event.signal}: "
        f"{event.old_value}->{event.new_value} cause={event.caused_by}"
    )
print(f"Sum={controller.simulation.read('Sum')} Cout={controller.simulation.read('Cout')}")
report = validate_full_adder_models()
print(f"Four-state comparison: {len(report.rows)} inputs, passed={report.passed}")
