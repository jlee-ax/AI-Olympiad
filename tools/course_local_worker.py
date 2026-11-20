"""One stateless lesson-author or reviewer call to a configured local model service."""
import ipaddress
import json
import os
import sys
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


ROLE_INSTRUCTIONS = (
    "Use the supplied KOAI role and evidence. Return one JSON object following the requested schema. "
    "Write student-facing lessons and exercises in Korean. Write all other documentation in English, "
    "including teacher-only notes, source summaries, review findings and reasons for changes. "
    "Preserve original source titles and quotations, identifiers and executable code when required. "
    "You have no filesystem or tools."
)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def main():
    task = json.load(sys.stdin)
    model = os.environ["COURSE_" + task["role"].upper() + "_MODEL"]
    endpoint = os.environ.get("COURSE_LOCAL_MODEL_URL", "http://127.0.0.1:11434/api/chat")
    parts = urlsplit(endpoint)
    if parts.scheme not in ("http", "https") or parts.username or parts.password:
        raise ValueError("Invalid local model endpoint")
    if parts.hostname != "localhost" and not ipaddress.ip_address(parts.hostname).is_loopback:
        raise ValueError("A loopback model service is required")
    body = {
        "model": model, "stream": False, "format": "json",
        "messages": [
            {"role": "system", "content": ROLE_INSTRUCTIONS},
            {"role": "user", "content": json.dumps(task, ensure_ascii=False)},
        ],
    }
    protocol = os.environ.get("COURSE_MODEL_PROTOCOL", "ollama")
    if protocol == "chat-completions":
        body.pop("format")
        body["response_format"] = {"type": "json_object"}
        effort = os.environ.get("COURSE_MODEL_EFFORT")
        if effort:
            body["reasoning_effort"] = effort
    elif protocol != "ollama":
        raise ValueError("Unknown model protocol")
    request = Request(endpoint, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with build_opener(ProxyHandler({}), NoRedirect()).open(request, timeout=600) as response:
        native = json.load(response)
    if native.get("model") != model:
        raise ValueError("The model service did not confirm the configured model/version")
    if protocol == "chat-completions":
        choice, = native["choices"]
        if choice["finish_reason"] != "stop":
            raise ValueError("Model output incomplete")
        content = choice["message"]["content"]
    else:
        if not native.get("done"):
            raise ValueError("Model output incomplete")
        content = native["message"]["content"]
    print(json.dumps(json.loads(content), ensure_ascii=False))


if __name__ == "__main__":
    main()
