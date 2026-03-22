from __future__ import annotations

from formal_hub.adapter import ReferenceProofAdapter
from formal_protocol import backend_capabilities


class RocqAdapter(ReferenceProofAdapter):
    def __init__(self) -> None:
        super().__init__(
            backend_id="rocq-local",
            kind="rocq",
            display_name="Rocq Local",
            languages=["rocq"],
            capabilities=backend_capabilities("rocq"),
            proof_hole_tokens=["Admitted", "admit"],
            native_tools={
                "build": "rocq-lsp",
                "proofSearch": "petanque",
                "dependencySlice": "fcc",
            },
        )
