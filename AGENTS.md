# AGENTS.md

This file is the persistent engineering memory for GlassMachine. It applies to the entire repository.

## Product identity

- Product: **GlassMachine**
- Tagline: **From Bit to Attention**
- Abbreviation: **GLASS** — **G**rounded, **L**ayered, **A**uditable **S**ystems **S**imulator
- Repository: `glass-machine`
- Python package: `glassmachine`
- License: MIT
- Do not abbreviate the project as `GM`; use `GLASS`.

## Mission

Build a Python-first, executable and auditable computer-systems laboratory that grows from transistor and gate-level local models into a complete small computer, then memory hierarchy, parallel computation, interconnects, accelerators, Attention and a tiny Transformer.

The project is memory- and data-movement-centric. At every scale it should help answer:

> Where did this data come from, where is it now, why did it move, what is it waiting for, where is it computed, and what changes under another architecture?

## Non-negotiable principles

1. **Simulation is the source of truth; visualization is not.**
   - UI actions call the simulation API.
   - The simulator changes state and emits events.
   - Visualization only renders state and events.
   - Never mutate architectural state inside drawing or animation code.

2. **Correctness must be independently grounded.**
   - Important modules require an explicit specification and ground truth.
   - Prefer an independent `ReferenceModel`, a transparent `DetailedModel`, and a scalable `FastModel` with the same contract.
   - Differentially test the models; do not derive every model from the same implementation.
   - External tools are welcome as additional oracles, not as unexplained authority.

3. **Every meaningful change must be auditable.**
   - State changes emit typed events with stable identity, time, source, destination, value and reason where applicable.
   - Runs must be deterministic under the same code, configuration, inputs and seed.
   - Experiments must be serializable and replayable.
   - Validation failures should identify the first divergent state or event.

4. **Layer detail; do not flatten or fake it.**
   - Support collapse and drill-down across system, component, RTL/gate and selected transistor detail.
   - Large simulations may use validated fast models.
   - A selected operation can be replayed with its real boundary inputs in a detailed model.
   - Explicitly document what each abstraction preserves and discards.

5. **Python is the public control surface.**
   - GUI and scripts use the same public simulation API.
   - The core must run headlessly.
   - Users must be able to define workloads, inspect state, add probes, run experiments and validate results from Python.

6. **Build progressively complete systems.**
   - Earlier validated components should remain meaningful foundations or reference baselines.
   - Do not create disconnected chapter demos that cannot participate in the growing system.
   - Keep simpler models available for learning and comparison after more detailed models are added.

7. **Memory and data movement are first-class.**
   - Model addresses, values, transactions, capacity, latency, bandwidth, granularity and queues explicitly.
   - Keep CPU data width, address width, memory transaction width, accelerator dtype and accumulator width independent.
   - Do not model SSD as a level visited by every load; it participates through file I/O, paging or explicit storage operations.

8. **Reimplement for understanding, reuse infrastructure.**
   - It is appropriate to reimplement mechanisms central to the learning and visualization goals.
   - Reuse GUI frameworks, test frameworks, numerical libraries, SPICE solvers and HDL simulators.
   - Before reimplementing a mechanism, document the learning question, project-specific need, abstraction boundary, ground truth and stopping point.
   - Respect licenses and record sources for copied or adapted code.

## Modeling layers and preferred tools

- Transistor-local: SPICE/ngspice adapters; do not build a general SPICE solver.
- Digital and RTL: Python structural models, PyRTL and/or limited Verilog; validate with an external HDL simulator when useful.
- CPU and system: Python state machines and deterministic discrete-event simulation.
- Memory and interconnect: Python transaction/event models with explicit timing and invariants.
- Tensor and Attention: transparent Python implementations plus NumPy/PyTorch references.
- Visualization: PySide6; it consumes traces and simulator state only.
- Tests: pytest and property/exhaustive testing where practical.

RTL is a selected detail layer, not the universal representation. It is appropriate for adders, registers, ALUs, datapaths, controllers, cache controllers, routers and accelerator-local logic. It is not the default representation for SSD behavior, OS paging, an entire LLM or analog transistor behavior.

## Architectural separation

Maintain clear dependency direction:

```text
visualization  ─┐
debugging      ─┼─> public simulation and trace APIs
validation     ─┘

simulation core must not depend on visualization
```

Keep these concerns separate:

- immutable specifications and contracts;
- architectural state;
- microarchitectural state;
- event/time progression;
- reference semantics;
- tracing, snapshots and replay;
- debugging controls;
- validation and invariants;
- rendering and animation;
- experiment configuration and reports.

## Validation requirements

Use the strongest practical validation for each layer:

- exhaustive truth tables for small Boolean components;
- exhaustive or property-based arithmetic tests for small-width datapaths;
- explicit transition tests for sequential state;
- independent ISA interpreter and instruction-boundary comparison for the CPU;
- bus-driver, width, request-lifecycle and protocol invariants during simulation;
- independent cache/reference models and fixed access traces;
- coherence litmus tests for multicore behavior;
- SPICE cross-checks for selected transistor circuits;
- PyRTL/Verilog simulation for selected RTL blocks;
- NumPy/PyTorch comparisons with declared dtype, rounding and tolerance for tensor computations;
- fixed weights, inputs and seeds for Transformer regression tests.

Distinguish claims carefully:

- functional truth: result matches the specification;
- protocol truth: transitions satisfy stated rules;
- model timing truth: execution follows declared latency/bandwidth parameters;
- hardware realism: requires measurement and calibration against a named real system.

Never claim real-hardware timing accuracy without calibration.

## Definition of done for a core module

A core module is not complete until it has, as applicable:

- a written specification and public contract;
- stated assumptions and abstraction losses;
- a ground-truth source;
- a reference implementation independent of the detailed implementation;
- tests covering normal, boundary and invalid behavior;
- deterministic trace events;
- validation or differential comparison;
- a headless experiment or reproducible test vector;
- visualization driven by the same real trace, when visualization is in scope;
- documentation of sources and licenses.

## Initial roadmap constraints

1. M0 establishes deterministic simulation, events, traces, replay, validation and a minimal visual surface.
2. The first vertical slice is a one-bit full adder with arbitrary inputs, transparent propagation, trace capture and reference/detailed/fast comparison.
3. Grow through multi-bit adder and register into a complete small CPU.
4. Design a small project-specific ISA only when entering the CPU/control milestone. Specify semantics before binary encoding, and provide an independent interpreter.
5. The 8-bit CPU is a scalar correctness baseline and future accelerator control plane, not a permanent global width restriction.
6. Expand next into memory hierarchy, then parallelism/interconnect, then matrix acceleration and Attention.

## Scope boundaries

Do not expand the near-term scope into:

- a full transistor-level CPU;
- physical chip layout or electromagnetic simulation;
- literal per-electron simulation;
- an exact clone of a commercial CPU/GPU;
- a general EDA or arbitrary-Verilog visualization tool;
- premature out-of-order execution, full operating systems or full RISC-V/x86 compatibility;
- 3D construction as the primary interaction;
- gate-level execution of a large LLM;
- decorative animation that does not correspond to a simulation event.

Use transistor detail to understand and ground selected local mechanisms. Prefer semantic truth over geometric realism.

## Engineering practices

- Keep the simulation core headless and deterministic.
- Prefer explicit typed data structures over unstructured dictionaries in core APIs.
- Keep units and widths explicit; validate them at boundaries.
- Make invalid states and unsupported behavior fail loudly.
- Preserve user-visible experiment and trace compatibility deliberately; version formats.
- Add a regression test for every fixed bug.
- Keep examples small enough to inspect and large enough to demonstrate the intended mechanism.
- Optimize only after correctness and trace semantics are established; retain the clear implementation as a reference when adding a fast path.
- Document design decisions that change a model's meaning, ground truth, preserved properties or scope.
