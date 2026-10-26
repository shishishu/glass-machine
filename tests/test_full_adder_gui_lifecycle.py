"""Catch native shutdown crashes that in-process widget tests cannot detect."""

import importlib.util
import os
import subprocess
import sys

import pytest


@pytest.mark.skipif(
    importlib.util.find_spec("PySide6") is None, reason="optional GUI not installed"
)
def test_full_adder_smoke_exits_cleanly_after_widget_teardown():
    environment = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
    # Repeat across fresh processes because the observed native teardown failure
    # was intermittent and happens after Python assertions have completed.
    for _ in range(3):
        result = subprocess.run(
            [sys.executable, "-m", "glassmachine", "gui", "--model", "full-adder", "--smoke"],
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert "shared QObject was deleted directly" not in result.stderr
