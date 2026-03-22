from __future__ import annotations

from formal_hub.adapter import ReferenceProofAdapter
from formal_protocol import backend_capabilities


class LeanAdapter(ReferenceProofAdapter):
    def __init__(self) -> None:
        super().__init__(
            backend_id="lean-local",
            kind="lean",
            display_name="Lean Local",
            languages=["lean"],
            capabilities=backend_capabilities("lean"),
            proof_hole_tokens=["admit", "sorry"],
            native_tools={
                "build": "lake",
                "proofSearch": "aesop",
                "dependencySlice": "lean-lsp",
            },
        )
