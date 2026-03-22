from __future__ import annotations

import json
from dataclasses import dataclass, field
import hashlib
import re
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from formal_protocol import PROTOCOL_VERSION


class ProofProtocolClientError(RuntimeError):
    pass


class HubTransport(Protocol):
    def call(self, method: str, params: dict[str, Any]) -> Any:
        raise NotImplementedError


class LocalHubTransport:
    def __init__(self, hub: Any):
        self.hub = hub
        self.request_id = 0

    def call(self, method: str, params: dict[str, Any]) -> Any:
        self.request_id += 1
        response = self.hub.handle_request({"jsonrpc": "2.0", "id": self.request_id, "method": method, "params": params})
        if "error" in response:
            raise ProofProtocolClientError(f"{response['error']['code']}: {response['error']['message']}")
        return response["result"]


class HttpHubTransport:
    def __init__(self, endpoint: str, *, auth_token: str | None = None, origin: str | None = None, timeout_seconds: float = 5.0):
        self.endpoint = endpoint
        self.auth_token = auth_token
        self.origin = origin
        self.timeout_seconds = timeout_seconds
        self.request_id = 0

    def call(self, method: str, params: dict[str, Any]) -> Any:
        self.request_id += 1
        payload = json.dumps({"jsonrpc": "2.0", "id": self.request_id, "method": method, "params": params}).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.auth_token is not None:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        if self.origin is not None:
            headers["Origin"] = self.origin
        request = Request(self.endpoint, data=payload, headers=headers, method="POST")
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except HTTPError as exc:
            raise ProofProtocolClientError(f"HTTP {exc.code}: {exc.reason}") from exc
        except URLError as exc:
            raise ProofProtocolClientError(f"Transport error: {exc.reason}") from exc
        data = json.loads(body)
        if "error" in data:
            raise ProofProtocolClientError(f"{data['error']['code']}: {data['error']['message']}")
        return data["result"]


@dataclass
class WorkspaceDocumentInput:
    uri: str
    language_id: str
    text: str


@dataclass
class ProofWorkspaceInputs:
    root_uri: str
    documents: list[WorkspaceDocumentInput] = field(default_factory=list)
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProofBuildRequest:
    """Caller-facing build request.

    `subject_id`, `subject_revision_id`, and `artifact_ref` are the canonical
    lower-seam correlation fields. Callers may map domain identities into them,
    but FWP should treat them as opaque metadata rather than protocol-owned
    assurance semantics.
    """

    request_id: str
    project_id: str
    subject_id: str
    subject_revision_id: str
    artifact_ref: str
    proof_source: str
    theorem_statement: str
    target_backend: str
    workspace_inputs: ProofWorkspaceInputs
    resource_policy: dict[str, Any]
    lineage: dict[str, Any]
    module_name: str = ""
    primary_target: str = ""
    run_kind: str = "build"

    @property
    def claim_id(self) -> str:
        return self.subject_id

    @property
    def claim_graph_revision_id(self) -> str:
        return self.subject_revision_id

    @property
    def formal_artifact_ref(self) -> str:
        return self.artifact_ref

    @property
    def target_theory(self) -> str:
        return self.module_name

    @property
    def target_theorem(self) -> str:
        return self.primary_target


@dataclass
class ProofAuditRequest:
    """Caller-facing audit request.

    The generic subject/artifact identifiers are opaque correlation metadata
    supplied by callers. Protocol consumers should not interpret them as
    FWP-owned assurance semantics.
    """

    request_id: str
    project_id: str
    subject_id: str
    subject_revision_id: str
    artifact_ref: str
    proof_source: str
    theorem_statement: str
    target_backend: str
    workspace_inputs: ProofWorkspaceInputs
    resource_policy: dict[str, Any]
    lineage: dict[str, Any]
    module_name: str = ""
    primary_target: str = ""
    export_requirements: list[str] = field(default_factory=list)
    trust_frontier_requirements: list[str] = field(default_factory=list)
    probe_requirements: list[str] = field(default_factory=list)
    robustness_harness_requirements: list[str] = field(default_factory=list)
    backend_extension_selection: dict[str, Any] = field(default_factory=dict)

    @property
    def claim_id(self) -> str:
        return self.subject_id

    @property
    def claim_graph_revision_id(self) -> str:
        return self.subject_revision_id

    @property
    def formal_artifact_ref(self) -> str:
        return self.artifact_ref

    @property
    def target_theory(self) -> str:
        return self.module_name

    @property
    def target_theorem(self) -> str:
        return self.primary_target


@dataclass
class ProofJobStatus:
    job_id: str
    status: str
    started_at: str | None
    completed_at: str | None
    workspace_ref: str
    artifact_refs: list[dict[str, Any]]
    diagnostic_summary: dict[str, Any]
    lineage: dict[str, Any]
    resource_usage: dict[str, Any]
    termination_reason: str | None
    backend_extensions: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProofAuditResult:
    workspace_ref: str
    contract_pack_ref: str
    signals: list[dict[str, Any]]
    lineage: dict[str, Any]
    backend_extensions: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProofArtifactIndex:
    workspace_ref: str
    artifacts: list[dict[str, Any]]


@dataclass
class ArtifactPayload:
    artifact_id: str
    content: str
    truncated: bool
    canonical: bool = True
    source: str = "artifact/read"


@dataclass
class ProofWorkspaceSnapshot:
    workspace_ref: str
    backend_id: str
    root_uri: str
    document_uris: list[str]
    targets: list[dict[str, Any]]
    artifacts: list[dict[str, Any]]


def _backend_family(backend_id: str) -> str:
    normalized = str(backend_id or "").strip().lower()
    if "lean" in normalized:
        return "lean"
    if "rocq" in normalized or "coq" in normalized:
        return "rocq"
    return "isabelle"


def _backend_extension(backend_id: str) -> str:
    return {
        "lean": ".lean",
        "rocq": ".v",
        "isabelle": ".thy",
    }[_backend_family(backend_id)]


def _backend_language_id(backend_id: str) -> str:
    return {
        "lean": "lean",
        "rocq": "coq",
        "isabelle": "isabelle",
    }[_backend_family(backend_id)]


def _safe_identifier(text: str, fallback: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", text or "").strip("_")
    if cleaned:
        return cleaned[:64]
    return fallback


def _synthesized_identifiers(
    request: ProofBuildRequest | ProofAuditRequest,
) -> tuple[str, str]:
    module_name = request.module_name.strip()
    primary_target = request.primary_target.strip()
    if not module_name:
        module_name = _safe_identifier(
            request.subject_id.replace(".", "_"),
            "FormalClaimModule",
        )
    if not primary_target:
        digest = hashlib.sha256(
            f"{request.subject_id}:{request.theorem_statement}".encode("utf-8")
        ).hexdigest()[:12]
        primary_target = _safe_identifier(
            request.theorem_statement.replace(" ", "_"),
            f"goal_{digest}",
        )
    return module_name, primary_target


def _synthesized_document_text(request: ProofBuildRequest | ProofAuditRequest) -> str:
    backend = _backend_family(request.target_backend)
    summary = request.proof_source.strip() or request.theorem_statement.strip() or "formal claim"
    target_name = request.primary_target or "target"
    module_name = request.module_name or "FormalClaim"
    if backend == "lean":
        return (
            f"/- {summary} -/\n\n"
            f"theorem {target_name} : True := by\n"
            f"  trivial\n"
        )
    if backend == "rocq":
        return (
            f"(* {summary} *)\n\n"
            f"Theorem {target_name} : True.\n"
            f"Proof.\n"
            f"  exact I.\n"
            f"Qed.\n"
        )
    return (
        f"theory {module_name}\n"
        f"  imports Main\n"
        f"begin\n\n"
        f"(* {summary} *)\n"
        f"theorem {target_name}: \"True\"\n"
        f"  by simp\n\n"
        f"end\n"
    )


def _synthesized_workspace_inputs(
    request: ProofBuildRequest | ProofAuditRequest,
) -> ProofWorkspaceInputs:
    module_name, primary_target = _synthesized_identifiers(request)
    extension = _backend_extension(request.target_backend)
    document_uri = request.workspace_inputs.root_uri.rstrip("/") + f"/{module_name}{extension}"
    document = WorkspaceDocumentInput(
        uri=document_uri,
        language_id=_backend_language_id(request.target_backend),
        text=_synthesized_document_text(request),
    )
    options = dict(request.workspace_inputs.options)
    options.setdefault("proofSource", request.proof_source)
    options.setdefault("theoremStatement", request.theorem_statement)
    options.setdefault("moduleName", module_name)
    options.setdefault("primaryTarget", primary_target)
    return ProofWorkspaceInputs(
        root_uri=request.workspace_inputs.root_uri,
        documents=[document],
        options=options,
    )


class ProofProtocolClient:
    def __init__(self, transport: HubTransport, *, client_name: str = "fwp-client", client_version: str = "0.1.0"):
        self.transport = transport
        self.client_name = client_name
        self.client_version = client_version
        self.initialized = False
        self.workspace_cache: dict[tuple[str, str], dict[str, Any]] = {}
        self.workspace_documents: dict[str, dict[str, WorkspaceDocumentInput]] = {}
        self.job_context: dict[str, dict[str, Any]] = {}
        self.artifact_context: dict[tuple[str, str], dict[str, Any]] = {}

    def initialize(self) -> dict[str, Any]:
        if self.initialized:
            return {"protocolVersion": PROTOCOL_VERSION, "reused": True}
        result = self.transport.call(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "clientInfo": {"name": self.client_name, "version": self.client_version},
                "capabilities": {"runGovernance": True, "rawPayload": False},
            },
        )
        self.initialized = True
        return result

    def submit_formalization_check(self, request: ProofBuildRequest) -> ProofJobStatus:
        self.initialize()
        module_name, primary_target = _synthesized_identifiers(request)
        workspace_inputs = _synthesized_workspace_inputs(request)
        workspace = self._ensure_workspace(request.target_backend, workspace_inputs)
        result = self.transport.call(
            "run.start",
            {
                "workspaceId": workspace["workspaceId"],
                "backendId": request.target_backend,
                "kind": request.run_kind,
                "target": self._target_ref(module_name, primary_target),
                "budget": dict(request.resource_policy),
            },
        )
        return self._remember_and_wrap_job(
            result,
            workspace_ref=workspace["workspaceId"],
            lineage=self._lineage_payload(request),
            artifact_ref=request.artifact_ref,
        )

    def submit_audit_probe(self, request: ProofAuditRequest) -> ProofAuditResult:
        self.initialize()
        module_name, primary_target = _synthesized_identifiers(request)
        workspace_inputs = _synthesized_workspace_inputs(request)
        workspace = self._ensure_workspace(request.target_backend, workspace_inputs)
        include = self._audit_include(request)
        result = self.transport.call(
            "audit/run",
            {
                "workspaceId": workspace["workspaceId"],
                "target": self._target_ref(module_name, primary_target),
                "include": include,
            },
        )
        return ProofAuditResult(
            workspace_ref=workspace["workspaceId"],
            contract_pack_ref=result["contractPackRef"],
            signals=result["signals"],
            lineage=self._lineage_payload(request),
            backend_extensions={"backend": request.target_backend, "selection": dict(request.backend_extension_selection)},
        )

    def get_job(self, job_id: str) -> ProofJobStatus:
        self.initialize()
        result = self.transport.call("run.poll", {"runId": job_id})
        return self._wrap_job(result)

    def cancel_job(self, job_id: str) -> ProofJobStatus:
        self.initialize()
        result = self.transport.call("run.cancel", {"runId": job_id})
        return self._wrap_job(result)

    def kill_job(self, job_id: str) -> ProofJobStatus:
        self.initialize()
        result = self.transport.call("run.kill", {"runId": job_id})
        return self._wrap_job(result)

    def get_workspace_snapshot(self, workspace_ref: str) -> ProofWorkspaceSnapshot:
        self.initialize()
        workspace = self._cached_workspace_by_id(workspace_ref)
        targets = self.transport.call("target/list", {"workspaceId": workspace_ref})
        return ProofWorkspaceSnapshot(
            workspace_ref=workspace_ref,
            backend_id=workspace["backendId"],
            root_uri=workspace["rootUri"],
            document_uris=sorted(self.workspace_documents.get(workspace_ref, {}).keys()),
            targets=targets,
            artifacts=self._merged_workspace_artifacts(workspace_ref),
        )

    def list_artifacts(self, workspace_ref: str) -> ProofArtifactIndex:
        self.initialize()
        return ProofArtifactIndex(workspace_ref=workspace_ref, artifacts=self._merged_workspace_artifacts(workspace_ref))

    def read_artifact(self, workspace_ref: str, artifact_id: str, *, max_bytes: int = 4096) -> ArtifactPayload:
        self.initialize()
        try:
            result = self.transport.call("artifact/read", {"workspaceId": workspace_ref, "artifactId": artifact_id, "maxBytes": max_bytes})
            return ArtifactPayload(
                artifact_id=result["artifactId"],
                content=result["content"],
                truncated=result["truncated"],
                canonical=True,
                source="artifact/read",
            )
        except ProofProtocolClientError:
            return self._read_run_artifact(workspace_ref, artifact_id, max_bytes=max_bytes)

    def _ensure_workspace(self, backend_id: str, workspace_inputs: ProofWorkspaceInputs) -> dict[str, Any]:
        key = (backend_id, workspace_inputs.root_uri)
        workspace = self.workspace_cache.get(key)
        if workspace is None:
            workspace = self.transport.call("workspace/open", {"rootUri": workspace_inputs.root_uri, "backendId": backend_id})
            self.workspace_cache[key] = workspace
            self.workspace_documents[workspace["workspaceId"]] = {}
        if workspace_inputs.options:
            self.transport.call("workspace/configure", {"workspaceId": workspace["workspaceId"], "options": dict(workspace_inputs.options)})
        for document in workspace_inputs.documents:
            self.transport.call(
                "document/open",
                {
                    "workspaceId": workspace["workspaceId"],
                    "uri": document.uri,
                    "languageId": document.language_id,
                    "text": document.text,
                },
            )
            self.workspace_documents[workspace["workspaceId"]][document.uri] = document
        return workspace

    def _remember_and_wrap_job(self, result: dict[str, Any], *, workspace_ref: str, lineage: dict[str, Any], artifact_ref: str) -> ProofJobStatus:
        self.job_context[result["runId"]] = {
            "workspaceRef": workspace_ref,
            "lineage": dict(lineage),
            "artifactRef": artifact_ref,
        }
        return self._wrap_job(result)

    def _wrap_job(self, result: dict[str, Any]) -> ProofJobStatus:
        context = self.job_context.get(result["runId"], {})
        self._remember_artifact_refs(result["runId"], context.get("workspaceRef"), result.get("artifactRefs", []))
        signals = result.get("signals", [])
        return ProofJobStatus(
            job_id=result["runId"],
            status=result["status"],
            started_at=result.get("timestamps", {}).get("startedAt"),
            completed_at=result.get("timestamps", {}).get("endedAt"),
            workspace_ref=context.get("workspaceRef", ""),
            artifact_refs=list(result.get("artifactRefs", [])),
            diagnostic_summary={"signalKinds": [signal["kind"] for signal in signals], "progress": dict(result.get("progress", {}))},
            lineage=dict(context.get("lineage", {})),
            resource_usage={"budget": dict(result.get("budget", {}))},
            termination_reason=self._termination_reason(result),
            backend_extensions={"backend": result.get("backend"), "kind": result.get("kind"), "artifactRef": context.get("artifactRef")},
        )

    def _cached_workspace_by_id(self, workspace_ref: str) -> dict[str, Any]:
        for workspace in self.workspace_cache.values():
            if workspace["workspaceId"] == workspace_ref:
                return workspace
        raise ProofProtocolClientError(f"Unknown workspaceRef {workspace_ref}")

    def _lineage_payload(self, request: ProofBuildRequest | ProofAuditRequest) -> dict[str, Any]:
        payload = dict(request.lineage)
        payload.setdefault("requestId", request.request_id)
        payload.setdefault("projectId", request.project_id)
        payload.setdefault("subjectId", request.subject_id)
        payload.setdefault("subjectRevisionId", request.subject_revision_id)
        payload.setdefault("artifactRef", request.artifact_ref)
        return payload

    def _target_ref(self, theory: str, theorem: str) -> dict[str, str]:
        return {"kind": "theorem", "ref": f"{theory}.{theorem}"}

    def _audit_include(self, request: ProofAuditRequest) -> list[str]:
        include = list(request.trust_frontier_requirements) + list(request.probe_requirements)
        if request.export_requirements:
            include.append("contractPack")
        if request.robustness_harness_requirements:
            include.append("probeSummaries")
        deduped = []
        for item in include or ["contractPack"]:
            if item not in deduped:
                deduped.append(item)
        return deduped

    def _termination_reason(self, result: dict[str, Any]) -> str | None:
        if result.get("status") == "running":
            return None
        signals = result.get("signals", [])
        if signals:
            return signals[0]["kind"]
        return result.get("status")

    def _merged_workspace_artifacts(self, workspace_ref: str) -> list[dict[str, Any]]:
        artifacts = list(self.transport.call("artifact/list", {"workspaceId": workspace_ref}))
        artifact_ids = {artifact["artifactId"] for artifact in artifacts}
        self._refresh_run_artifacts(workspace_ref)
        for (candidate_workspace, artifact_id), context in sorted(self.artifact_context.items()):
            if candidate_workspace != workspace_ref or artifact_id in artifact_ids:
                continue
            artifacts.append(dict(context["artifactRef"]))
            artifact_ids.add(artifact_id)
        return artifacts

    def _refresh_run_artifacts(self, workspace_ref: str) -> None:
        for job_id, context in sorted(self.job_context.items()):
            if context.get("workspaceRef") != workspace_ref:
                continue
            result = self.transport.call("run.artifacts", {"runId": job_id})
            self._remember_artifact_refs(job_id, workspace_ref, result.get("artifacts", []))

    def _remember_artifact_refs(self, run_id: str, workspace_ref: str | None, artifact_refs: list[dict[str, Any]]) -> None:
        if workspace_ref is None:
            return
        for artifact_ref in artifact_refs:
            self.artifact_context[(workspace_ref, artifact_ref["artifactId"])] = {
                "runId": run_id,
                "workspaceRef": workspace_ref,
                "artifactRef": dict(artifact_ref),
            }

    def _read_run_artifact(self, workspace_ref: str, artifact_id: str, *, max_bytes: int) -> ArtifactPayload:
        context = self.artifact_context.get((workspace_ref, artifact_id))
        if context is None:
            raise ProofProtocolClientError(f"Unknown artifact {artifact_id} for workspace {workspace_ref}")
        logs = self.transport.call("run.logs", {"runId": context["runId"]})
        lines = [f"run artifact {artifact_id}", *logs.get("logs", [])]
        artifact_ref = context["artifactRef"]
        if artifact_ref.get("uri"):
            lines.append(f"uri: {artifact_ref['uri']}")
        content, truncated = self._truncate_content("\n".join(lines), max_bytes)
        return ArtifactPayload(
            artifact_id=artifact_id,
            content=content,
            truncated=truncated,
            canonical=False,
            source="run.logs-fallback",
        )

    def _truncate_content(self, content: str, max_bytes: int) -> tuple[str, bool]:
        raw = content.encode("utf-8")
        if len(raw) <= max_bytes:
            return content, False
        return raw[:max_bytes].decode("utf-8", errors="ignore"), True
