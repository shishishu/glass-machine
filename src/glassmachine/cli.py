"""Command-line entry points for NOT and full-adder experiments."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from glassmachine.core.errors import GlassMachineError
from glassmachine.core.logic import LogicValue
from glassmachine.experiments.not_gate import ExperimentRecord, InputStep, NotExperiment
from glassmachine.validation.not_gate import validate_not_models


def _logic_values(text: str) -> tuple[LogicValue, ...]:
    try:
        return tuple(LogicValue.parse(part.strip()) for part in text.split(",") if part.strip())
    except GlassMachineError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="glassmachine",
        description="GlassMachine — Grounded, Layered, Auditable Systems Simulator",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    not_parser = subparsers.add_parser("not", help="run the reproducible M0 NOT experiment")
    not_parser.add_argument("--inputs", type=_logic_values, default=_logic_values("0,1,X,Z"))
    not_parser.add_argument("--delay", type=int, default=1)
    not_parser.add_argument("--spacing", type=int, default=2)
    not_parser.add_argument("--trace", type=Path)
    not_parser.add_argument("--record", type=Path)

    adder_parser = subparsers.add_parser("full-adder", help="run the M1 five-gate full adder")
    for name in ("a", "b", "cin"):
        adder_parser.add_argument(f"--{name}", default="0", choices=("0", "1", "X", "Z"))
    adder_parser.add_argument("--delay", type=int, default=1)
    adder_parser.add_argument("--trace", type=Path)
    adder_parser.add_argument("--record", type=Path)
    verify_parser = subparsers.add_parser("verify", help="exhaustively compare models")
    verify_parser.add_argument("--model", choices=("not", "full-adder"), default="not")

    replay_parser = subparsers.add_parser("replay", help="recompute a recorded experiment")
    replay_parser.add_argument("record", type=Path)
    replay_parser.add_argument("--trace", type=Path)

    gui_parser = subparsers.add_parser("gui", help="open an optional PySide6 circuit visualizer")
    gui_parser.add_argument("--model", choices=("not", "full-adder"), default="not")
    gui_parser.add_argument(
        "--smoke",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    return parser


def _run_not(args: argparse.Namespace) -> int:
    if args.spacing <= 0:
        raise ValueError("--spacing must be positive")
    steps = tuple(
        InputStep(time=index * args.spacing, value=value)
        for index, value in enumerate(args.inputs)
    )
    experiment = NotExperiment(steps=steps, delay=args.delay)
    result = experiment.run()
    for event in result.trace:
        print(
            f"t={event.time:<3} delta={event.delta:<2} id={event.event_id:<3} "
            f"{event.kind.value:<14} {event.signal}: {event.old_value}->{event.new_value} "
            f"cause={event.caused_by}"
        )
    print(f"output={result.output} trace={result.trace.digest()}")
    if args.trace:
        result.trace.write_jsonl(args.trace)
        print(f"wrote trace: {args.trace}")
    if args.record:
        ExperimentRecord.capture(experiment).write_json(args.record)
        print(f"wrote experiment record: {args.record}")
    return 0


def _verify() -> int:
    report = validate_not_models()
    for row in report.rows:
        print(
            f"input={row.input_value.value} reference={row.reference} "
            f"detailed={row.detailed} fast={row.fast} passed={row.passed}"
        )
    print("M0 NOT validation: PASS")
    return 0


def _run_full_adder(args: argparse.Namespace) -> int:
    from glassmachine.experiments.full_adder import AdderInput, FullAdderExperiment, FullAdderRecord

    experiment = FullAdderExperiment(
        tuple(
            AdderInput(0, signal, LogicValue.parse(value))
            for signal, value in (("A", args.a), ("B", args.b), ("Cin", args.cin))
        ),
        delay=args.delay,
    )
    simulation = experiment.run()
    for event in simulation.trace:
        print(
            f"t={event.time} delta={event.delta} id={event.event_id} "
            f"{event.signal}: {event.old_value}->{event.new_value} cause={event.caused_by}"
        )
    print(
        f"Sum={simulation.read('Sum')} Cout={simulation.read('Cout')} "
        f"trace={simulation.trace.digest()}"
    )
    if args.trace:
        simulation.trace.write_jsonl(args.trace)
    if args.record:
        FullAdderRecord.capture(experiment).write_json(args.record)
    return 0


def _verify_full_adder() -> int:
    from glassmachine.validation.full_adder import validate_full_adder_models

    report = validate_full_adder_models()
    for row in report.rows:
        print(
            f"A={row.a} B={row.b} Cin={row.cin} "
            f"reference={row.reference.sum}/{row.reference.carry} "
            f"detailed={row.detailed.sum}/{row.detailed.carry} "
            f"fast={row.fast.sum}/{row.fast.carry} passed={row.passed}"
        )
    print("M1 full-adder validation: PASS (64 four-state inputs)")
    return 0


def _replay(args: argparse.Namespace) -> int:
    payload = json.loads(args.record.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("experiment record must be an object")
    if payload.get("kind") == "full-adder":
        from glassmachine.experiments.full_adder import FullAdderRecord

        simulation = FullAdderRecord.read_json(args.record).replay()
        if args.trace:
            simulation.trace.write_jsonl(args.trace)
        print(
            f"replay: PASS Sum={simulation.read('Sum')} Cout={simulation.read('Cout')} "
            f"trace={simulation.trace.digest()}"
        )
        return 0
    record = ExperimentRecord.read_json(args.record)
    result = record.replay()
    if args.trace:
        result.trace.write_jsonl(args.trace)
    print(f"replay: PASS output={result.output} trace={result.trace.digest()}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "not":
            return _run_not(args)
        if args.command == "full-adder":
            return _run_full_adder(args)
        if args.command == "verify":
            return _verify_full_adder() if args.model == "full-adder" else _verify()
        if args.command == "replay":
            return _replay(args)
        if args.command == "gui":
            if args.model == "full-adder":
                from glassmachine.visualization.full_adder_demo import run_full_adder_demo

                return int(run_full_adder_demo(smoke=args.smoke))
            from glassmachine.visualization.not_demo import run_not_demo

            return int(run_not_demo(smoke=args.smoke))
    except (GlassMachineError, RuntimeError, ValueError, OSError) as exc:
        print(f"glassmachine: error: {exc}", file=sys.stderr)
        return 2
    return 2
