"""Run with: PYTHONPATH=src python examples/not_gate.py"""

from glassmachine.core.logic import LogicValue
from glassmachine.models.digital.detailed.not_gate import build_not_simulation

simulation = build_not_simulation(delay=1)
simulation.trace.clear()

for value in LogicValue:
    simulation.set_input("input", value)
    simulation.run_until_stable()
    print(f"NOT {value.value} = {simulation.read('output')}")

print(f"trace digest: {simulation.trace.digest()}")
