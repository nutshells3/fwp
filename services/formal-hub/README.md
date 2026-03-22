# formal-hub

The FWP hub brokers requests between clients and backend adapters, maintains
workspace state, records transcripts, and enforces run governance.

This service is a reference and conformance surface inside the FWP repo.
In the target stack, authoritative proof-host execution belongs to
`proof-assistant`, not to `formal-hub`.

Default behavior is to delegate to sibling `proof-assistant` when available.
There is no repo-local runtime fallback anymore. If `proof-assistant` is not
available, `formal-hub` fails fast instead of pretending to be a proof host.

Current implementation notes:

- normalized event notifications are emitted for build, goals, diagnostics,
  probe, and audit updates
- subscription queues are bounded and can be drained by hub-level tests
- transcript export plus replay harness support deterministic conformance tests
