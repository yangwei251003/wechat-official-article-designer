from __future__ import annotations

import argparse
import hashlib
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

SCENARIOS = {"success", "token-expired", "ip-denied", "permission-denied", "rate-limit", "invalid-image", "draft-error"}


class MockState:
    def __init__(self, scenario: str = "success") -> None:
        if scenario not in SCENARIOS:
            raise ValueError(f"未知Mock场景：{scenario}")
        self.scenario = scenario
        self.idempotency: dict[str, dict[str, Any]] = {}

    def response_for(self, method: str, path: str, body: dict[str, Any] | None, *, idempotency_key: str) -> tuple[int, dict[str, Any]]:
        if self.scenario == "token-expired":
            return 200, {"errcode": 40014, "errmsg": "invalid access_token"}
        if self.scenario == "ip-denied":
            return 200, {"errcode": 40164, "errmsg": "invalid ip"}
        if self.scenario == "permission-denied":
            return 200, {"errcode": 48001, "errmsg": "api unauthorized"}
        if self.scenario == "rate-limit":
            return 200, {"errcode": 45009, "errmsg": "reach max api daily quota limit"}
        if path.startswith("/cgi-bin/token") and method == "GET":
            return 200, {"access_token": "mock-access-token", "expires_in": 7200}
        if path.startswith("/cgi-bin/media/uploadimg") and method == "POST":
            if self.scenario == "invalid-image":
                return 200, {"errcode": 40007, "errmsg": "invalid media_id"}
            return 200, {"url": "https://mmbiz.qpic.cn/mock/inline/0"}
        if path.startswith("/cgi-bin/material/add_material") and method == "POST":
            return 200, {"media_id": "mock-cover", "url": "https://mmbiz.qpic.cn/mock/cover/0"}
        if path.startswith("/cgi-bin/draft/add") and method == "POST":
            if self.scenario == "draft-error":
                return 200, {"errcode": 44003, "errmsg": "empty news data"}
            fingerprint = idempotency_key or hashlib.sha256(json.dumps(body or {}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            if fingerprint not in self.idempotency:
                self.idempotency[fingerprint] = {"media_id": f"mock-draft-{fingerprint[:12]}", "mock": True}
            return 200, self.idempotency[fingerprint]
        return 404, {"errcode": 404, "errmsg": "mock route not found"}


def handler_factory(state: MockState):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args) -> None:
            return

        def _send(self, payload: dict[str, Any], status: int) -> None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:
            status, payload = state.response_for("GET", self.path, None, idempotency_key=self.headers.get("X-Idempotency-Key", ""))
            self._send(payload, status)

        def do_POST(self) -> None:
            length = min(int(self.headers.get("Content-Length", "0")), 5 * 1024 * 1024)
            raw = self.rfile.read(length)
            try:
                body = json.loads(raw.decode("utf-8")) if self.headers.get("Content-Type", "").startswith("application/json") and raw else {}
            except json.JSONDecodeError:
                body = {}
            status, payload = state.response_for("POST", self.path, body, idempotency_key=self.headers.get("X-Idempotency-Key", ""))
            self._send(payload, status)

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser(description="仅绑定本机的微信公众号API Mock服务")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--scenario", choices=sorted(SCENARIOS), default="success")
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler_factory(MockState(args.scenario)))
    print(f"http://127.0.0.1:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
