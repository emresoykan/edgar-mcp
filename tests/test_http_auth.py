import unittest

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from http_auth import BearerTokenMiddleware


def _app():
    async def ok(_request):
        return JSONResponse({"ok": True})

    inner = Starlette(routes=[Route("/mcp", ok, methods=["POST"]), Route("/health", ok)])
    return BearerTokenMiddleware(inner, "secret-token")


class BearerAuthTests(unittest.TestCase):
    def test_health_is_public(self):
        client = TestClient(_app())
        res = client.get("/health")
        self.assertEqual(res.status_code, 200)

    def test_mcp_rejects_missing_token(self):
        client = TestClient(_app())
        res = client.post("/mcp")
        self.assertEqual(res.status_code, 401)

    def test_mcp_accepts_bearer(self):
        client = TestClient(_app())
        res = client.post("/mcp", headers={"Authorization": "Bearer secret-token"})
        self.assertEqual(res.status_code, 200)


if __name__ == "__main__":
    unittest.main()
