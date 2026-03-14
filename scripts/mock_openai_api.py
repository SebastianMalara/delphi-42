from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


DEFAULT_MODEL = os.environ.get("MOCK_OPENAI_MODEL", "qwen3-1.7B-Int8-ctx-axcl")
DEFAULT_PORT = int(os.environ.get("MOCK_OPENAI_PORT", "8000"))
API_PREFIX = os.environ.get("MOCK_OPENAI_API_PREFIX", "/v1")


class MockOpenAIHandler(BaseHTTPRequestHandler):
    server_version = "Delphi42MockOpenAI/0.1"

    def do_GET(self) -> None:
        status, payload = _route_request("GET", self.path)
        self._write_json(status, payload)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8") if length else "{}"
        payload = json.loads(body or "{}")
        status, response_payload = _route_request("POST", self.path, payload)
        self._write_json(status, response_payload)

    def log_message(self, format: str, *args) -> None:
        return None

    def _write_json(self, status: int, payload: dict) -> None:
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


def _normalize_api_prefix(raw_prefix: str) -> str:
    prefix = raw_prefix.strip() or "/v1"
    if not prefix.startswith("/"):
        prefix = "/" + prefix
    return prefix.rstrip("/") or "/v1"


def _api_path(suffix: str) -> str:
    normalized_prefix = _normalize_api_prefix(API_PREFIX)
    normalized_suffix = suffix if suffix.startswith("/") else f"/{suffix}"
    return f"{normalized_prefix}{normalized_suffix}"


def _route_request(method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
    if method == "GET" and path == _api_path("/models"):
        return (
            200,
            {
                "object": "list",
                "data": [
                    {
                        "id": DEFAULT_MODEL,
                        "object": "model",
                        "owned_by": "delphi-42-mock",
                    }
                ],
            },
        )

    if method == "POST" and path == _api_path("/chat/completions"):
        payload = payload or {}
        prompt = _last_user_message(payload.get("messages", []))
        short_answer, long_answer = _draft_from_prompt(prompt)
        content = f"SHORT: {short_answer}\nLONG:\n{long_answer}"
        return (
            200,
            {
                "id": "chatcmpl-delphi42-mock",
                "object": "chat.completion",
                "model": payload.get("model", DEFAULT_MODEL),
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": content,
                        },
                        "finish_reason": "stop",
                    }
                ],
            },
        )

    return 404, {"error": {"message": "not found"}}


def _last_user_message(messages: list[dict]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            content = message.get("content", "")
            return content if isinstance(content, str) else str(content)
    return ""


def _draft_from_prompt(prompt: str) -> tuple[str, str]:
    context = _extract_context(prompt)
    if not context or context == "(no matching passages)":
        return (
            "The archive does not contain a grounded answer yet.",
            "The archive does not contain a grounded answer yet.",
        )

    first_line = context.splitlines()[0].removeprefix("- ").strip()
    short_answer = first_line.split(":", maxsplit=1)[-1].strip() or first_line
    short_answer = short_answer[:117].rstrip()
    if len(first_line) > 117:
        short_answer = f"{short_answer}..."
    return short_answer, first_line


def _extract_context(prompt: str) -> str:
    marker = "Context:\n"
    question_marker = "\n\nQuestion:\n"
    if marker not in prompt or question_marker not in prompt:
        return ""
    return prompt.split(marker, maxsplit=1)[1].split(question_marker, maxsplit=1)[0].strip()


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", DEFAULT_PORT), MockOpenAIHandler)
    print(f"mock openai api listening on :{DEFAULT_PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
