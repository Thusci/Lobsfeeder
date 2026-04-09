from __future__ import annotations

from app.clients.openai_compat_client import OpenAICompatClient
from app.core.settings import AppConfig


class ClientRegistry:
    def __init__(self, config: AppConfig) -> None:
        self._clients: dict[str, OpenAICompatClient] = {
            model_key: OpenAICompatClient(model_key=model_key, config=model_cfg)
            for model_key, model_cfg in config.models.items()
        }

    def get(self, model_key: str) -> OpenAICompatClient:
        return self._clients[model_key]

    async def aclose_all(self) -> None:
        for client in self._clients.values():
            await client.aclose()
