from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from formal_protocol.assets import PROTOCOL_VERSION


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class HubError(Exception):
    def __init__(self, code: str, message: str, *, retryable: bool = False, data: dict[str, Any] | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.data = data or {}


class ReferenceProofAdapter:
    def __init__(
        self,
        *,
        backend_id: str,
        kind: str,
        display_name: str,
        languages: list[str],
        capabilities: dict[str, Any],
        proof_hole_tokens: list[str],
        native_tools: dict[str, str],
    ) -> None:
        self.backend_id = backend_id
        self.kind = kind
        self.display_name = display_name
        self.languages = languages
        self.capabilities = capabilities
        self.proof_hole_tokens = proof_hole_tokens
        self.native_tools = native_tools
        self.workspaces: dict[str, dict[str, Any]] = {}

    def descriptor(self) -> dict[str, Any]:
        return {
            "backendId": self.backend_id,
            "kind": self.kind,
            "displayName": self.display_name,
            "version": "0.1.0",
            "protocolVersion": PROTOCOL_VERSION,
            "languages": self.languages,
            "capabilities": self.capabilities,
            "transport": {"kind": "stdio"},
            "argv": ["python", "-m", f"{self.kind}_adapter"],
        }

    def supports_probe(self, probe_kind: str) -> bool:
        return bool(self.capabilities["probes"].get(probe_kind, False))

    def supports_query(self, query_name: str) -> bool:
        return bool(self.capabilities["queries"].get(query_name, False))

    def open_workspace(self, root_uri: str, connection_source: str = "descriptor") -> dict[str, Any]:
        workspace_id = f"ws_{self.kind}"
        self.workspaces[workspace_id] = {
            "workspaceId": workspace_id,
            "rootUri": root_uri,
            "backendId": self.backend_id,
            "connectionSource": connection_source,
            "openedAt": utc_now(),
            "documents": {},
            "artifacts": {},
            "snapshots": {},
        }
        return {
            "workspaceId": workspace_id,
            "rootUri": root_uri,
            "backendId": self.backend_id,
            "connectionSource": connection_source,
            "openedAt": self.workspaces[workspace_id]["openedAt"],
        }

    def configure_workspace(self, workspace_id: str, options: dict[str, Any]) -> dict[str, Any]:
        workspace = self._workspace(workspace_id)
        workspace["config"] = dict(options)
        return {"workspaceId": workspace_id, "configured": True, "options": dict(options)}

    def close_workspace(self, workspace_id: str) -> dict[str, Any]:
        self._workspace(workspace_id)
        del self.workspaces[workspace_id]
        return {"workspaceId": workspace_id, "closed": True}

    def open_document(self, workspace_id: str, uri: str, language_id: str, text: str) -> dict[str, Any]:
        workspace = self._workspace(workspace_id)
        document_id = self._document_id(uri)
        workspace["documents"][document_id] = {
            "documentId": document_id,
            "workspaceId": workspace_id,
            "uri": uri,
            "languageId": language_id,
            "version": 1,
            "syncMode": "incremental",
            "text": text,
        }
        return self._public_document(workspace["documents"][document_id])

    def change_document(self, workspace_id: str, document_id: str, text: str) -> dict[str, Any]:
        document = self._document(workspace_id, document_id)
        document["version"] += 1
        document["text"] = text
        return self._public_document(document)

    def save_document(self, workspace_id: str, document_id: str) -> dict[str, Any]:
        document = self._document(workspace_id, document_id)
        snapshot_id = f"snap_{document_id}_{document['version']}"
        workspace = self._workspace(workspace_id)
        workspace["snapshots"][snapshot_id] = {
            "snapshotId": snapshot_id,
            "workspaceId": workspace_id,
            "documentId": document_id,
            "backendOpaqueRef": f"{self.kind}:{snapshot_id}",
        }
        return dict(workspace["snapshots"][snapshot_id])

    def close_document(self, workspace_id: str, document_id: str) -> dict[str, Any]:
        workspace = self._workspace(workspace_id)
        self._document(workspace_id, document_id)
        del workspace["documents"][document_id]
        return {"documentId": document_id, "closed": True}

    def list_targets(self, workspace_id: str) -> list[dict[str, Any]]:
        workspace = self._workspace(workspace_id)
        targets = []
        for document in workspace["documents"].values():
            targets.append({"kind": "document", "ref": document["uri"], "workspaceId": workspace_id})
        return targets

    def build_run(self, workspace_id: str, target: dict[str, Any], budget: dict[str, Any] | None = None) -> dict[str, Any]:
        workspace = self._workspace(workspace_id)
        content = self._target_text(workspace_id, target)
        artifact_id = f"artifact_{self.kind}_build_log"
        artifact = {
            "artifactId": artifact_id,
            "kind": "build-log",
            "uri": f"artifact://{self.kind}/build-log",
            "content": f"{self.display_name} build for {target['ref']} succeeded\n{content[:120]}",
        }
        workspace["artifacts"][artifact_id] = artifact
        return {
            "status": "ok",
            "artifacts": [self._artifact_ref(artifact)],
            "rawPayload": {"backend": self.kind, "tool": self.native_tools.get("build", "build"), "budget": budget or {}},
        }

    def list_artifacts(self, workspace_id: str) -> list[dict[str, Any]]:
        return [self._artifact_ref(item) for item in self._workspace(workspace_id)["artifacts"].values()]

    def read_artifact(self, workspace_id: str, artifact_id: str, max_bytes: int | None = None) -> dict[str, Any]:
        artifact = self._artifact(workspace_id, artifact_id)
        content = artifact["content"]
        truncated = False
        if max_bytes is not None and len(content.encode("utf-8")) > max_bytes:
            truncated = True
            content = content.encode("utf-8")[:max_bytes].decode("utf-8", errors="ignore")
        return {"artifactId": artifact_id, "content": content, "truncated": truncated}

    def export_artifact(self, workspace_id: str, artifact_id: str) -> dict[str, Any]:
        artifact = self._artifact(workspace_id, artifact_id)
        return {"artifactId": artifact_id, "exportUri": artifact["uri"], "kind": artifact["kind"]}

    def query(self, workspace_id: str, query_name: str, target: dict[str, Any]) -> dict[str, Any]:
        if not self.supports_query(query_name):
            raise HubError("CapabilityError", f"{self.kind} does not support query/{query_name}")
        text = self._target_text(workspace_id, target)
        if query_name == "goals":
            return {"goals": [{"goalId": f"{self.kind}_goal_1", "summary": f"1. {target['ref']}", "facts": self._facts(text)}]}
        if query_name == "diagnostics":
            diagnostics = []
            for token in self.proof_hole_tokens:
                if token in text:
                    diagnostics.append({"severity": "warning", "message": f"contains {token}", "uri": target["ref"]})
            return {"diagnostics": diagnostics}
        if query_name == "hover":
            return {"contents": f"{self.display_name} symbol information for {target['ref']}"}
        if query_name == "definition":
            return {"symbol": target["ref"], "definition": f"definition of {target['ref']}"}
        if query_name == "type":
            return {"symbol": target["ref"], "type": "Prop"}
        if query_name == "dependencies":
            return {"target": target["ref"], "dependencies": self._facts(text)}
        if query_name == "status":
            return {"target": target["ref"], "status": "clean"}
        raise HubError("ProtocolError", f"Unknown query/{query_name}")

    def probe_run(self, workspace_id: str, target: dict[str, Any], probe_kind: str, implementation: dict[str, Any] | None = None, options: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.supports_probe(probe_kind):
            raise HubError("CapabilityError", f"{self.kind} does not support probe {probe_kind}")
        text = self._target_text(workspace_id, target)
        if probe_kind == "counterexample":
            outcome = "found" if any(token in text for token in self.proof_hole_tokens) or "False" in text else "none"
            summary = "Counterexample found" if outcome == "found" else "No counterexample found"
            normalized = {"outcome": outcome}
        elif probe_kind == "proofSearch":
            summary = "Found candidate proof"
            normalized = {"outcome": "candidate", "steps": ["simp", "exact"]}
        elif probe_kind == "dependencySlice":
            summary = "Dependency slice created"
            normalized = {"dependencies": self._facts(text)}
        else:
            summary = f"{probe_kind} completed"
            normalized = {"outcome": "completed", "probe": probe_kind}
        return {
            "probeRunId": f"probe_{self.kind}_{probe_kind}",
            "kind": probe_kind,
            "status": "completed",
            "summary": summary,
            "normalizedResult": normalized,
            "rawPayload": {"backend": self.kind, "tool": (implementation or {}).get("tool", self.native_tools.get(probe_kind, probe_kind)), "options": options or {}},
        }

    def audit_run(self, workspace_id: str, target: dict[str, Any], include: list[str]) -> dict[str, Any]:
        text = self._target_text(workspace_id, target)
        signals = []
        if "trustFrontier" in include:
            signals.append({"kind": "trustFrontier", "status": "trusted" if self.kind == "isabelle" else "backend-defined"})
        if "dependencySlice" in include:
            signals.append({"kind": "dependencySlice", "dependencies": self._facts(text)})
        if "probeSummaries" in include:
            signals.append({"kind": "probeSummary", "summary": "simulated"})
        return {
            "workspaceId": workspace_id,
            "target": target,
            "signals": signals,
            "contractPackRef": f"contract-pack://{self.kind}/{target['ref'].replace('.', '-')}",
            "rawPayload": {"backend": self.kind, "include": include},
        }

    def governed_run_result(self, kind: str, target: dict[str, Any], budget: dict[str, Any]) -> dict[str, Any]:
        text = self._target_text(target.get("workspaceId", f"ws_{self.kind}"), target, allow_empty=True)
        artifact = {"artifactId": f"artifact_{self.kind}_{kind}", "kind": "run-log", "uri": f"artifact://{self.kind}/{kind}", "content": f"{kind} run for {target['ref']}\n{text[:120]}"}
        return {"status": "completed", "progress": {"percent": 100, "message": f"{kind} completed"}, "signals": [{"kind": "success"}], "artifactRefs": [self._artifact_ref(artifact)], "logs": [f"Started {kind}", f"Finished {kind}"]}

    def backend_extension(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        return {"backend": self.kind, "method": method, "params": params, "status": "ok"}

    def _workspace(self, workspace_id: str) -> dict[str, Any]:
        workspace = self.workspaces.get(workspace_id)
        if workspace is None:
            raise HubError("WorkspaceError", f"Unknown workspace {workspace_id}")
        return workspace

    def _document(self, workspace_id: str, document_id: str) -> dict[str, Any]:
        document = self._workspace(workspace_id)["documents"].get(document_id)
        if document is None:
            raise HubError("DocumentError", f"Unknown document {document_id}")
        return document

    def _artifact(self, workspace_id: str, artifact_id: str) -> dict[str, Any]:
        artifact = self._workspace(workspace_id)["artifacts"].get(artifact_id)
        if artifact is None:
            raise HubError("BuildError", f"Unknown artifact {artifact_id}")
        return artifact

    def _document_id(self, uri: str) -> str:
        return "doc_" + Path(uri).name.replace(".", "_").lower()

    def _public_document(self, document: dict[str, Any]) -> dict[str, Any]:
        return {key: document[key] for key in ["documentId", "workspaceId", "uri", "languageId", "version", "syncMode"]}

    def _artifact_ref(self, artifact: dict[str, Any]) -> dict[str, Any]:
        return {"artifactId": artifact["artifactId"], "kind": artifact["kind"], "uri": artifact["uri"]}

    def _target_text(self, workspace_id: str, target: dict[str, Any], allow_empty: bool = False) -> str:
        workspace = self.workspaces.get(workspace_id, {})
        if target.get("kind") == "document":
            for document in workspace.get("documents", {}).values():
                if document["uri"] == target["ref"] or document["documentId"] == target["ref"]:
                    return document["text"]
        if target.get("kind") == "theorem":
            theorem_ref = str(target.get("ref") or "")
            theory_name = theorem_ref.split(".", 1)[0] if theorem_ref else ""
            for document in workspace.get("documents", {}).values():
                stem = Path(document["uri"]).stem
                if theory_name and stem == theory_name:
                    return document["text"]
        return "" if allow_empty else f"theorem {target['ref']}"

    def _facts(self, text: str) -> list[str]:
        facts = []
        for line in text.splitlines():
            if line.startswith("imports ") or line.startswith("Require Import"):
                facts.extend(line.split()[1:])
            if "simp" in line:
                facts.append("simp")
            if "trivial" in line:
                facts.append("trivial")
        return facts or ["Main"]
