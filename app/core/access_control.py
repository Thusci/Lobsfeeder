from __future__ import annotations

from copy import deepcopy
from ipaddress import ip_address, ip_network
from typing import Any, Iterable

from fastapi import Request


SECRET_PLACEHOLDER = "********"


DEFAULT_ADMIN_ALLOWED_CIDRS = [
    "127.0.0.0/8",
    "::1/128",
    "10.0.0.0/8",
    "172.16.0.0/12",
    "192.168.0.0/16",
    "fc00::/7",
    "fe80::/10",
]


def validate_cidrs(values: Iterable[str]) -> list[str]:
    normalized: list[str] = []
    for value in values:
        network = ip_network(str(value).strip(), strict=False)
        normalized.append(str(network))
    return normalized


def request_client_host(request: Request) -> str | None:
    if request.client is None:
        return None
    return request.client.host


def is_host_allowed(host: str | None, cidrs: Iterable[str]) -> bool:
    if not host:
        return False
    try:
        address = ip_address(host)
    except ValueError:
        return False

    networks = [ip_network(cidr, strict=False) for cidr in cidrs]
    return any(address in network for network in networks)


def is_admin_path(path: str) -> bool:
    return path == "/ui" or path.startswith("/ui/") or path == "/admin" or path.startswith("/admin/")


def redact_config(config: Any) -> dict[str, Any]:
    data = config.model_dump() if hasattr(config, "model_dump") else deepcopy(config)
    server = data.get("server")
    if isinstance(server, dict):
        _redact_secret_list(server, "router_api_keys")
        _redact_secret_list(server, "admin_api_keys")

    models = data.get("models")
    if isinstance(models, dict):
        for model in models.values():
            if isinstance(model, dict) and model.get("api_key"):
                model["api_key"] = SECRET_PLACEHOLDER

    return data


def merge_redacted_secrets(payload: dict[str, Any], current_config: Any) -> dict[str, Any]:
    current = current_config.model_dump() if hasattr(current_config, "model_dump") else deepcopy(current_config)
    merged = deepcopy(payload)

    incoming_server = merged.get("server")
    current_server = current.get("server") if isinstance(current, dict) else None
    if isinstance(incoming_server, dict) and isinstance(current_server, dict):
        _merge_secret_list(incoming_server, current_server, "router_api_keys")
        _merge_secret_list(incoming_server, current_server, "admin_api_keys")

    incoming_models = merged.get("models")
    current_models = current.get("models") if isinstance(current, dict) else None
    if isinstance(incoming_models, dict) and isinstance(current_models, dict):
        for model_key, incoming_model in incoming_models.items():
            current_model = current_models.get(model_key)
            if not isinstance(incoming_model, dict) or not isinstance(current_model, dict):
                continue
            if incoming_model.get("api_key") == SECRET_PLACEHOLDER:
                incoming_model["api_key"] = current_model.get("api_key")

    return merged


def _redact_secret_list(data: dict[str, Any], key: str) -> None:
    values = data.get(key)
    if isinstance(values, list):
        data[key] = [SECRET_PLACEHOLDER for value in values if str(value).strip()]


def _merge_secret_list(incoming: dict[str, Any], current: dict[str, Any], key: str) -> None:
    incoming_values = incoming.get(key)
    current_values = current.get(key)
    if not isinstance(incoming_values, list) or not isinstance(current_values, list):
        return

    merged: list[Any] = []
    for index, value in enumerate(incoming_values):
        if value == SECRET_PLACEHOLDER:
            if index < len(current_values):
                merged.append(current_values[index])
            continue
        merged.append(value)
    incoming[key] = merged
