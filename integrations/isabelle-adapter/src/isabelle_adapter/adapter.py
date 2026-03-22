from __future__ import annotations

from formal_hub.adapter import ReferenceProofAdapter
from formal_protocol import backend_capabilities


class IsabelleAdapter(ReferenceProofAdapter):
    def __init__(self) -> None:
        super().__init__(
            backend_id="isabelle-local",
            kind="isabelle",
            display_name="Isabelle Local",
            languages=["isabelle"],
            capabilities=backend_capabilities("isabelle"),
            proof_hole_tokens=["sorry", "oops"],
            native_tools={
                "build": "isabelle-build",
                "counterexample": "nitpick",
                "proofSearch": "sledgehammer",
                "dependencySlice": "dump",
            },
        )

    def build_run(self, workspace_id: str, target: dict, budget: dict | None = None) -> dict:
        text = self._target_text(workspace_id, target)
        raw = self._runner_build(target["ref"], text)
        result = super().build_run(workspace_id, target, budget)
        result["rawPayload"]["runner"] = raw
        return result

    def probe_run(self, workspace_id: str, target: dict, probe_kind: str, implementation: dict | None = None, options: dict | None = None) -> dict:
        text = self._target_text(workspace_id, target)
        result = super().probe_run(workspace_id, target, probe_kind, implementation, options)
        if probe_kind == "counterexample":
            result["rawPayload"]["runner"] = self._runner_nitpick(target["ref"], text)
        elif probe_kind == "proofSearch":
            result["rawPayload"]["runner"] = self._runner_sledgehammer(target["ref"], text)
        return result

    def _runner_build(self, target_ref: str, text: str) -> dict:
        return {"tool": "build", "target": target_ref, "status": "ok", "content": text}

    def _runner_nitpick(self, target_ref: str, text: str) -> dict:
        found = "sorry" in text or "False" in text
        return {"tool": "nitpick", "target": target_ref, "found": found}

    def _runner_sledgehammer(self, target_ref: str, text: str) -> dict:
        return {"tool": "sledgehammer", "target": target_ref, "steps": ["simp", "blast"]}
