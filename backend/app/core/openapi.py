"""Post-process OpenAPI schema to document runtime success/error envelopes."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


def _success_response_schema(data_schema: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["success", "data"],
        "properties": {
            "success": {"type": "boolean", "const": True},
            "data": data_schema,
            "message": {"anyOf": [{"type": "string"}, {"type": "null"}]},
            "meta": {
                "anyOf": [
                    {"type": "object", "additionalProperties": True},
                    {"type": "null"},
                ],
            },
        },
    }


def _error_response_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["success", "error"],
        "properties": {
            "success": {"type": "boolean", "const": False},
            "error": {
                "type": "object",
                "required": ["code", "message", "status_code"],
                "properties": {
                    "code": {"type": "string"},
                    "message": {"type": "string"},
                    "details": {},
                    "status_code": {"type": "integer"},
                },
            },
            "meta": {
                "anyOf": [
                    {"type": "object", "additionalProperties": True},
                    {"type": "null"},
                ],
            },
        },
    }


def apply_envelope_openapi(schema: dict[str, Any]) -> dict[str, Any]:
    """Wrap JSON success responses and attach standard error responses."""
    updated = deepcopy(schema)
    components = updated.setdefault("components", {})
    schemas = components.setdefault("schemas", {})
    schemas.setdefault("SuccessResponseEnvelope", _success_response_schema({"type": "object"}))
    schemas["ErrorResponseEnvelope"] = _error_response_schema()

    for path_item in updated.get("paths", {}).values():
        if not isinstance(path_item, dict):
            continue
        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue
            responses = operation.get("responses")
            if not isinstance(responses, dict):
                continue

            for status_code, response in list(responses.items()):
                if not str(status_code).startswith("2"):
                    continue
                if not isinstance(response, dict):
                    continue
                content = response.get("content")
                if not isinstance(content, dict):
                    continue
                json_content = content.get("application/json")
                if not isinstance(json_content, dict):
                    continue
                inner_schema = json_content.get("schema")
                if not isinstance(inner_schema, dict):
                    continue
                json_content["schema"] = _success_response_schema(deepcopy(inner_schema))

            for status_code in ("400", "401", "403", "404", "409", "422", "429", "500", "503"):
                if status_code not in responses:
                    responses[status_code] = {
                        "description": "Error response envelope",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponseEnvelope"},
                            },
                        },
                    }

    return updated
