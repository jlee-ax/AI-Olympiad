"""Run the published Week 1 notebook from blank outputs and check its HTML handout."""
import argparse
import base64
import copy
import hashlib
import json
import os
import shutil
import struct
import tempfile
from pathlib import Path
from urllib.parse import unquote, urlsplit

import nbformat
from bs4 import BeautifulSoup
from nbconvert import HTMLExporter

from course_kernel import execute_notebook

ROOT = Path(__file__).resolve().parents[1]
LESSON = ROOT / "lessons/week01"
STEM = "week01_integrated"
READING_CSS = """
body.jp-Notebook {
  --jp-content-font-family: "Noto Sans CJK KR", "Noto Sans CJK JP", "Apple SD Gothic Neo", "Malgun Gothic", sans-serif;
}
.jp-MarkdownCell .jp-Cell-inputWrapper { display: block; padding-left: var(--jp-cell-prompt-width); }
.jp-MarkdownCell .jp-InputArea { display: block; width: auto; }
.jp-MarkdownCell .jp-InputArea-prompt { display: none; }
.jp-MarkdownCell .jp-RenderedMarkdown { display: block; box-sizing: border-box; max-width: 100%; overflow-x: auto; }
@media (max-width: 600px) {
  body.jp-Notebook { padding: 8px; }
  .jp-MarkdownCell .jp-Cell-inputWrapper { padding-left: 0; }
  .jp-Cell .jp-Cell-inputWrapper, .jp-Cell .jp-Cell-outputWrapper,
  .jp-Cell .jp-InputArea, .jp-Cell .jp-OutputArea-child { display: block; }
  .jp-Cell .jp-InputArea-prompt, .jp-Cell .jp-OutputArea-prompt { display: none; }
  .jp-Cell .jp-InputArea-editor, .jp-Cell .jp-OutputArea-output,
  .jp-Cell .jp-RenderedMarkdown {
    display: block; box-sizing: border-box; min-width: 0; max-width: 100%; overflow-x: auto;
  }
  .jp-Cell img { max-width: 100%; height: auto; }
}
"""


def source_digest(notebook):
    cells = []
    for cell in notebook.cells:
        material = dict(cell)
        for field in ("outputs", "execution_count"):
            material.pop(field, None)
        material["metadata"] = {k: v for k, v in cell.metadata.items() if k != "execution"}
        cells.append(material)
    return hashlib.sha256(json.dumps(cells, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def render(notebook):
    title = next(line[2:].strip() for cell in notebook.cells if cell.cell_type == "markdown"
                 for line in cell.source.splitlines() if line.startswith("# "))
    html, _ = HTMLExporter(language_code="ko").from_notebook_node(
        notebook, resources={"metadata": {"name": title}})
    doc = BeautifulSoup(html, "html.parser")
    markdown = "\n".join(c.source for c in notebook.cells if c.cell_type == "markdown")
    has_math_or_diagrams = any(marker in markdown for marker in ("$", r"\(", r"\[", "```mermaid"))
    has_interactive_output = any(
        any(key.startswith(("application/javascript", "application/vnd.jupyter")) for key in o.get("data", {}))
        for c in notebook.cells for o in c.get("outputs", []))
    if not has_math_or_diagrams and not has_interactive_output:
        for script in doc.head.select("script"):
            script.decompose()
    meta = doc.new_tag("meta", attrs={"name": "koai-notebook-source-sha256", "content": source_digest(notebook)})
    doc.head.append(meta)
    style = doc.new_tag("style", id="week01-reading-layout")
    style.string = READING_CSS
    doc.head.append(style)
    for cell in notebook.cells:
        if cell.cell_type != "code":
            continue
        images = doc.find(id="cell-id=" + cell.id).select(".jp-RenderedImage img")
        if images:
            descriptions = cell.metadata.get("figure_alt")
            descriptions = [descriptions] if isinstance(descriptions, str) else descriptions
            if not isinstance(descriptions, list) or len(images) != len(descriptions) or not all(descriptions):
                raise ValueError(f"{cell.id}: add a figure_alt description for every output image")
            for image, description in zip(images, descriptions):
                image["alt"] = description
    return doc


def visible_cells(doc, *, image_bytes):
    cells = []
    for cell in doc.select("main .jp-Cell"):
        content = cell.select_one(".jp-MarkdownOutput, .jp-InputArea-editor pre")
        outputs = cell.select(".jp-OutputArea-output")
        links = [a.get("href") for a in content.select("a[href]")]
        pictures = []
        for image in cell.select(".jp-OutputArea-output img"):
            prefix, _, encoded = image["src"].partition(",")
            raw = base64.b64decode(encoded, validate=True)
            if prefix != "data:image/png;base64" or raw[:8] != bytes.fromhex("89504e470d0a1a0a"):
                raise ValueError(f"{cell.get('id')}: expected an embedded PNG")
            if min(struct.unpack(">II", raw[16:24])) < 100:
                raise ValueError(f"{cell.get('id')}: empty or undersized figure")
            pictures.append((image.get("alt"), hashlib.sha256(raw).hexdigest() if image_bytes else None))
        # Adjacent stdout chunks can be grouped differently by kernel transports.
        output = " ".join(" ".join(part.stripped_strings) for part in outputs)
        cells.append((cell["id"], content.get_text().strip(), links, " ".join(output.split()), pictures))
    return cells


def check_links(doc, lesson):
    local = set()
    for anchor in doc.select("main a[href]"):
        href = urlsplit(anchor["href"])
        if href.scheme or href.netloc:
            continue
        if href.path:
            relative = unquote(href.path)
            if not (lesson / relative).is_file():
                raise ValueError(f"Missing lesson resource: {relative}")
            local.add(relative)
        elif href.fragment and not any(doc.find(id=k) for k in (href.fragment, unquote(href.fragment))):
            raise ValueError(f"Missing page anchor: {href.fragment}")
    return sorted(local)


def verify(source, fresh, published):
    nbformat.validate(fresh)
    authored = source_digest(source)
    if authored != source_digest(fresh):
        raise ValueError("Execution changed the authored cells")
    code = [c for c in fresh.cells if c.cell_type == "code"]
    if [c.execution_count for c in code] != list(range(1, len(code) + 1)):
        raise ValueError("Code cells were not all run in order")
    for cell in code:
        if any(o.output_type == "error" or o.get("name") == "stderr" for o in cell.outputs):
            raise ValueError(f"{cell.id}: inspect kernel error or warning output")
        has_code = any(line.strip() and not line.lstrip().startswith("#") for line in cell.source.splitlines())
        if not has_code and cell.outputs:
            raise ValueError(f"{cell.id}: a blank exercise has saved output")
    doc = render(fresh)
    committed = BeautifulSoup(published, "html.parser")
    for page in (doc, committed):
        meta = page.select_one('meta[name="koai-notebook-source-sha256"]')
        if (page.html.get("lang") != "ko" or page.title.get_text() != doc.title.get_text()
                or not meta or meta.get("content") != authored):
            raise ValueError("HTML language, title or authored-source fingerprint is stale")
    style = committed.find("style", id="week01-reading-layout")
    if not style or style.string != READING_CSS:
        raise ValueError("Published reading layout differs from the current export")
    if visible_cells(render(source), image_bytes=True) != visible_cells(committed, image_bytes=True):
        raise ValueError("Published HTML differs from the notebook's saved cells, outputs, links or PNGs")
    if visible_cells(doc, image_bytes=False) != visible_cells(committed, image_bytes=False):
        raise ValueError("Fresh execution differs from the published cells, text, tables or figure descriptions")
    figures = doc.select(".jp-OutputArea-output img")
    tables = doc.select(".jp-OutputArea-output table")
    if len(figures) < 2 or not tables:
        raise ValueError("Expected the worked scatter plot, grouped bar plot and output tables")
    plan = BeautifulSoup((ROOT / "curriculum/student-plan.html").read_text(), "html.parser")
    entry = "https://github.com/jlee-ax/AI-Olympiad/blob/main/lessons/week01/" + STEM + ".ipynb"
    if [a["href"] for a in plan.select('#week-1 a[href$=".ipynb"]')] != [entry]:
        raise ValueError("The student plan must open the maintained Week 1 notebook")
    return {"authored_cells_sha256": authored, "code_cells": len(code), "figures": len(figures),
            "output_tables": len(tables), "local_resources": check_links(committed, LESSON)}


def browser_check(path, executable):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=executable or None)
        for width in (1280, 390):
            page = browser.new_page(viewport={"width": width, "height": 850})
            page.route("https://**/*", lambda route: route.abort())
            page.goto(path.resolve().as_uri(), wait_until="load")
            page.locator("h1").wait_for()
            if page.evaluate("document.documentElement.scrollWidth") > width + 1:
                raise ValueError(f"Page overflows the {width}px viewport")
            opening = page.locator(".jp-RenderedMarkdown").first
            if not opening.evaluate("""element => Array.from(element.querySelectorAll('h1, p')).every(node => {
                const range = document.createRange(); range.selectNodeContents(node);
                return Array.from(range.getClientRects()).every(r => r.left >= 0 && r.right <= innerWidth + 1);
            })"""):
                raise ValueError(f"Opening prose is clipped at {width}px")
            for figure in page.locator(".jp-RenderedImage img").all():
                figure.scroll_into_view_if_needed()
                if not figure.evaluate("img => img.complete && img.naturalWidth > 0 && img.clientWidth > 0"):
                    raise ValueError(f"A figure did not display at {width}px")
            page.close()
        browser.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, help="Save the newly executed notebook and HTML here")
    parser.add_argument("--browser", nargs="?", const="", metavar="EXECUTABLE",
                        help="Open the HTML in Playwright Chromium or a supplied executable")
    args = parser.parse_args()
    source = nbformat.read(LESSON / (STEM + ".ipynb"), as_version=4)
    blank = copy.deepcopy(source)
    for cell in blank.cells:
        if cell.cell_type == "code":
            cell.outputs, cell.execution_count = [], None
            cell.metadata.pop("execution", None)
    # Build the font index before stdout/stderr is attached to a student cell.
    from matplotlib import font_manager
    font_manager.findfont(font_manager.FontProperties())
    os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")
    with tempfile.TemporaryDirectory(prefix="week01-kernel-") as temp:
        directory = Path(temp)
        for csv in LESSON.rglob("*.csv"):
            target = directory / csv.relative_to(LESSON)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(csv, target)
        fresh = execute_notebook(blank, directory)
    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        nbformat.write(fresh, args.output_dir / (STEM + ".ipynb"))
        (args.output_dir / (STEM + ".html")).write_text(str(render(fresh)), encoding="utf-8")
    path = LESSON / (STEM + ".html")
    receipt = verify(source, fresh, path.read_text(encoding="utf-8"))
    if args.browser is not None:
        browser_check(path, args.browser)
        receipt["browser_widths"] = [1280, 390]
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
