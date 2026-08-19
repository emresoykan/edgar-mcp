"""Optional Bearer token gate for the public Railway HTTP app."""

from __future__ import annotations

import json
from typing import Any

PUBLIC_PATHS = frozenset({"/", "/health"})


class BearerTokenMiddleware:
    """Rejects MCP routes unless Authorization matches `Bearer <token>`.

    Lifespan and WebSocket scopes pass through. `/` and `/health` stay public
    so Railway healthchecks work without the token.
    """

    def __init__(self, app: Any, token: str) -> None:
        self.app = app
        self.token = token.strip()

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] != "http" or not self.token:
            await self.app(scope, receive, send)
            return
        if scope.get("method") == "OPTIONS" or scope.get("path") in PUBLIC_PATHS:
            await self.app(scope, receive, send)
            return
        headers = {
            key.decode("latin1").lower(): value.decode("latin1")
            for key, value in scope.get("headers") or []
        }
        if headers.get("authorization") == f"Bearer {self.token}":
            await self.app(scope, receive, send)
            return
        body = json.dumps({"error": "unauthorized"}).encode()
        await send(
            {
                "type": "http.response.start",
                "status": 401,
                "headers": [(b"content-type", b"application/json")],
            }
        )
        await send({"type": "http.response.body", "body": body})
