"""Reference-only FWP hub surfaces for conformance tests and seam validation."""

from .adapter import HubError, ReferenceProofAdapter
from .hub import build_reference_hub
from .transcripts import ReplayHarness, TranscriptRecorder

__all__ = [
    "HubError",
    "ReferenceProofAdapter",
    "ReplayHarness",
    "TranscriptRecorder",
    "build_reference_hub",
]
