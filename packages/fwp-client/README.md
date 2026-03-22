# fwp-client

Reference proof-protocol client for the FWP seam.

This package is the intended upper dependency point for `formal-claim` style
callers. It supports:

- local in-process transport through a hub object
- remote HTTP transport to an FWP server
- a backend-neutral `ProofProtocolClient` facade for build, audit, job control,
  workspace snapshot, and artifact access
- a merged artifact view that includes workspace artifacts and governed-run
  postmortem or run-log outputs behind the same upper-layer API

It does not own claim, assurance, or promotion semantics.

Any claim-oriented identifiers carried in request DTOs are opaque caller
correlation metadata. FWP transports them but does not own their semantics.

When `artifact/read` is unavailable for a governed-run artifact, the client may
surface a non-canonical fallback synthesized from `run.logs`. That payload is
explicitly marked as non-canonical by the client API.
