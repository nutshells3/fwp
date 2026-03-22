from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from formal_protocol import ValidationError, validate_method_params, validate_method_result

from .adapter import HubError
from .transcripts import TranscriptRecorder


def _activate_sibling_proof_assistant() -> None:
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent.parent.parent.parent / "proof-assistant" / "src"
        if candidate.exists():
            text = str(candidate)
            if text not in sys.path:
                sys.path.insert(0, text)
            return


class _ValidatedDelegateHub:
    def __init__(self, delegate: Any) -> None:
        self._delegate = delegate
        self.recorder = TranscriptRecorder()
        self._patch_notify()

    def _patch_notify(self) -> None:
        original_notify = getattr(self._delegate, "_notify", None)
        if original_notify is None:
            return

        def wrapped_notify(method: str, params: dict[str, Any]) -> None:
            self.recorder.record(
                "notification",
                {"jsonrpc": "2.0", "method": method, "params": params},
            )
            original_notify(method, params)

        self._delegate._notify = wrapped_notify  # type: ignore[attr-defined]

    def handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        request_id = request.get("id")
        try:
            self._validate_request(request)
            self.recorder.record("request", request)
            response = self._delegate.handle_request(request)
            if "result" in response:
                response = {
                    **response,
                    "result": self._normalize_result(request["method"], response["result"]),
                }
            if "result" in response:
                validate_method_result(request["method"], response["result"])
            self.recorder.record("response", response, for_method=request["method"])
            return response
        except HubError as exc:
            response = self._error_response(
                request_id,
                exc.code,
                exc.message,
                retryable=exc.retryable,
                data=exc.data,
            )
            self.recorder.record("response", response, for_method=request.get("method"))
            return response
        except Exception as exc:  # pragma: no cover
            response = self._error_response(
                request_id,
                "BackendInternalError",
                str(exc),
                retryable=False,
                data={},
            )
            self.recorder.record("response", response, for_method=request.get("method"))
            return response

    def drain_subscription_events(self, subscription_id: str) -> list[dict[str, Any]]:
        try:
            return self._delegate.drain_subscription_events(subscription_id)
        except Exception as exc:
            code = getattr(exc, "code", "ProtocolError")
            message = getattr(exc, "message", str(exc))
            retryable = bool(getattr(exc, "retryable", False))
            data = dict(getattr(exc, "data", {}) or {})
            raise HubError(code, message, retryable=retryable, data=data) from exc

    def _validate_request(self, request: dict[str, Any]) -> None:
        if not isinstance(request, dict):
            raise HubError("ProtocolError", "Request must be an object")
        if request.get("jsonrpc") != "2.0":
            raise HubError("ProtocolError", "jsonrpc must be 2.0")
        if "method" not in request:
            raise HubError("ProtocolError", "Request missing method")
        if not isinstance(request["method"], str):
            raise HubError("ProtocolError", "method must be a string")
        if "id" not in request:
            raise HubError("ProtocolError", "Request missing id")
        if not isinstance(request.get("params", {}), dict):
            raise HubError("ProtocolError", "params must be an object")
        if len(json.dumps(request)) > 200_000:
            raise HubError("ResourceError", "Oversized message payload")
        try:
            validate_method_params(request["method"], request.get("params", {}))
        except ValidationError as exc:
            raise HubError(
                "ProtocolError",
                f"Invalid params for {request['method']}: {exc}",
            ) from exc

    def _error_response(
        self,
        request_id: Any,
        code: str,
        message: str,
        *,
        retryable: bool,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message,
                "retryable": retryable,
                "data": data,
            },
        }

    def __getattr__(self, name: str) -> Any:
        return getattr(self._delegate, name)

    def _normalize_result(self, method: str, result: Any) -> Any:
        if not isinstance(result, dict):
            return result
        if method == "build/run":
            result.pop("policyEnvelope", None)
            return result
        if method in {"run.start", "run.poll", "run.cancel", "run.kill"}:
            result.pop("profileName", None)
            return result
        return result


def build_reference_hub() -> Any:
    _activate_sibling_proof_assistant()
    try:
        from proof_assistant.server import build_hub as build_proof_assistant_hub  # type: ignore
    except (ImportError, ModuleNotFoundError) as exc:
        raise RuntimeError(
            "proof-assistant delegate is unavailable; "
            "formal-hub no longer ships a repo-local runtime fallback."
        ) from exc
    return _ValidatedDelegateHub(build_proof_assistant_hub())
