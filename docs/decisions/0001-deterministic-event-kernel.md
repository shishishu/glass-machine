# ADR 0001: deterministic event kernel

- Status: accepted
- Date: 2026-08-30

## Context

GlassMachine needs causal visualization, event-level debugging, stable replay and later support for
gate delay, clocks, memory requests and interconnect traffic. Direct recursive updates would make
results depend on Python call order and would not provide a durable audit trail.

## Decision

Use a central discrete-event kernel. Order scheduled work by integer `(time, delta, sequence)` and
emit an immutable event only after a value change commits. Components are pure with respect to
simulation state. Visualization consumes the resulting trace.

## Consequences

- Runs are deterministic and replayable.
- Zero-delay propagation is explicit through delta cycles.
- Oscillation can be detected with a finite event budget.
- Every state change has an event identity and causal parent.
- The model is not yet calibrated to real physical time.
