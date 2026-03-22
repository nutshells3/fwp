# fwp-mcp-bridge

Thin MCP-facing allowlisted bridge over the FWP hub.

Current implementation notes:

- allowlisted tools are schema-validated before they reach the hub
- tool results are sanitized and revalidated after redaction
- descriptor and transcript resources are exposed as read-only sanitized views
