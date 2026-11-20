"""Refresh primary documents used by the course into a private JSON packet.

Markdown, HTML, Jupyter and PDF are projected to readable text. The controller
binds the original byte digest, locator and exact supplied text independently.
"""
import argparse
import hashlib
import html.parser
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


class VisibleHTML(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.drop = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.drop += 1
        if tag in ("p", "tr", "li", "h1", "h2", "h3"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.drop:
            self.drop -= 1
        if tag == "td":
            self.parts.append(" | ")

    def handle_data(self, text):
        if not self.drop:
            self.parts.append(text)


def fetch(locator, pages):
    target = locator
    parts = urlsplit(locator)
    if parts.scheme != "https" or parts.username or parts.password:
        raise ValueError("Expected a public HTTPS primary locator")
    if parts.hostname == "github.com" and "/blob/" in parts.path:
        target = "https://raw.githubusercontent.com" + parts.path.replace("/blob/", "/", 1)
    with urlopen(Request(target, headers={"User-Agent": "KOAI-course-material-review"}), timeout=40) as response:
        data = response.read(32 * 1024 * 1024 + 1)
        if len(data) > 32 * 1024 * 1024:
            raise ValueError("Primary document exceeds the bounded reader limit")
        content_type = response.headers.get_content_type()
        final = response.geturl()
    if target.endswith(".ipynb"):
        nb = json.loads(data)
        text = "\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "markdown")
        text = re.sub(r"data:image/[^)\s\"']+", "[embedded figure]", text)
    elif data.startswith(b"%PDF"):
        parts = []
        for limits in pages or [None]:
            flags = ["-f", str(limits[0]), "-l", str(limits[1])] if limits else []
            parts.append(subprocess.run(["pdftotext", *flags, "-layout", "-", "-"], input=data, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, timeout=45, check=True).stdout.decode())
        text = "\n".join(parts)
    elif content_type == "text/html":
        parser = VisibleHTML()
        parser.feed(data.decode("utf-8"))
        text = "".join(parser.parts)
    else:
        text = data.decode("utf-8")
    return {"locator": locator, "resolved_url": final, "bytes": len(data),
            "original_sha256": hashlib.sha256(data).hexdigest(), "text": text}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design", type=Path, default=Path("curriculum/course-harness.json"))
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    output = args.out.resolve()
    if output.is_relative_to(Path(__file__).resolve().parents[1]):
        raise SystemExit("Store primary extracts in private run storage outside the repository")
    design = json.loads(args.design.read_text())
    records = {}
    for name, source in design["sources"].items():
        pages = source.get("primary_pages", [])
        item = fetch(source["locator"], pages)
        item["pages"] = pages
        lines = item.pop("text").splitlines()
        bounds = source.get("primary_lines")
        if bounds:
            first, last = bounds
            if not 1 <= first <= last <= len(lines):
                raise ValueError("Stale primary line selection for " + name)
        else:
            first, last = 1, len(lines)
        selected = "\n".join(lines[first - 1:last]).strip()
        if not selected or len(selected) > 180000:
            raise ValueError("Supply bounded primary_lines for " + name)
        records[name] = {**item, "lines": [first, last], "text": selected}
    with tempfile.NamedTemporaryFile("w", encoding="utf8", dir=output.parent, delete=False) as f:
        try:
            json.dump(records, f, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
            temporary = f.name
        except BaseException:
            os.unlink(f.name)
            raise
    os.replace(temporary, output)


if __name__ == "__main__":
    main()
