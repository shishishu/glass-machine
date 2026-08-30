"""Command-line entry points for the M0 experiment and verification loop."""

from __future__ import annotations

import argparse
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

    subparsers.add_parser("verify", help="exhaustively compare all M0 NOT models")

    replay_parser = subparsers.add_parser("replay", help="recompute a recorded experiment")
    replay_parser.add_argument("record", type=Path)
    replay_parser.add_argument("--trace", type=Path)

    gui_parser = subparsers.add_parser("gui", help="open the optional PySide6 NOT visualizer")
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


def _replay(args: argparse.Namespace) -> int:
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
        if args.command == "verify":
            return _verify()
        if args.command == "replay":
            return _replay(args)
        if args.command == "gui":
            from glassmachine.visualization.not_demo import run_not_demo

            return run_not_demo(smoke=args.smoke)
    except (GlassMachineError, RuntimeError, ValueError) as exc:
        print(f"glassmachine: error: {exc}", file=sys.stderr)
        return 2
    return 2
