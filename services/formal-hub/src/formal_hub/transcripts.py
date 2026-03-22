from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class TranscriptRecorder:
    def __init__(self) -> None:
        self.steps: list[dict[str, Any]] = []

    def record(self, kind: str, message: dict[str, Any], *, for_method: str | None = None) -> None:
        step = {"kind": kind, "message": message}
        if for_method is not None:
            step["forMethod"] = for_method
        self.steps.append(step)

    def export(self, path: Path, name: str) -> None:
        path.write_text(json.dumps({"name": name, "steps": self.steps}, indent=2) + "\n", encoding="utf-8")


class ReplayHarness:
    def __init__(self, transcript: dict[str, Any]) -> None:
        self.transcript = transcript
        self.index = 0

    def next(self) -> dict[str, Any]:
        if self.index >= len(self.transcript["steps"]):
            raise IndexError("Replay transcript exhausted")
        step = self.transcript["steps"][self.index]
        self.index += 1
        return step
