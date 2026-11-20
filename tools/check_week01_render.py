"""Execute the registered Week 1 notebooks and verify their downloadable and offline-reading editions."""
import argparse
import base64
import binascii
import copy
import hashlib
import json
from io import BytesIO, StringIO
import os
import shutil
import struct
import tempfile
from html import escape
from pathlib import Path
from urllib.parse import unquote, urlsplit

from jinja2 import pass_context
from latex2mathml.converter import convert as mathml

import nbformat
from nbclient import NotebookClient
from bs4 import BeautifulSoup
import numpy as np
from PIL import Image, ImageFilter
from nbconvert import HTMLExporter
from nbconvert.filters.markdown_mistune import IPythonRenderer, MarkdownWithMath


ROOT = Path(__file__).resolve().parents[1]
LESSON = ROOT / "lessons/week01"
STEM = "week01_integrated"
NOTEBOOK_DATA_URL = "data:application/octet-stream;base64,"
# Each worked-code ID identifies its notebook even when an external validator supplies an in-memory copy.
REQUIRED_PROFILES = {
    STEM: ("484f22ba", 3, 5),
    "week01_python_tables": ("d2be9ce3", 5, 11),
    "week01_axes_linear_bridge": ("ba428b91", 0, 0),
    "week01_problem_pipeline": ("622155d2", 0, 2),
}
ANSWERS = {
    STEM: {"gallery-challenge-work", "records-work", "summary-exercise-work", "e49ac1c2", "exercise-validation-answer", "rectangle-independent-answer"},
    "week01_python_tables": {"modify-mean-function", "depth-reshape-code", "practice-broadcast-code",
                            "depth-function-code", "tables-csv-work", "digits-csv-work", "tables-prediction-work"},
    "week01_axes_linear_bridge": {"7b96a39e", "54646dc1"},
    "week01_problem_pipeline": {"06ceb97e", "device-score-work"},
}
READING_CSS = """
.week01-navigation {
  display: flex; flex-wrap: wrap; gap: 8px 24px; margin: 8px 16px 12px;
  font: 15px/1.5 "Noto Sans CJK KR", "Noto Sans CJK JP", sans-serif;
}
.week01-figure-view, .week01-figure-scroll { display: block; max-width: 100%; }
.week01-figure-scroll { overflow-x: auto; }
.week01-figure-toggle, .week01-figure-label { display: none; }
.jp-RenderedMarkdown math[display="block"] { max-width: 100%; overflow-x: auto; }
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
  .week01-figure-toggle, .week01-figure-label { display: inline-block; }
  .week01-figure-label { cursor: pointer; margin: 4px 0 6px 4px; font: 14px/1.5 sans-serif; }
  .week01-figure-toggle:checked ~ .week01-figure-scroll img { width: auto; max-width: none; }
}
"""


def registered_handouts(lesson):
    manifest = json.loads((lesson / "lesson-manifest.json").read_text(encoding="utf-8"))
    registry = {}
    for member in manifest["current_release"]["members"].values():
        student, html = Path(member["student"]), Path(member["html"])
        if (student.parent != Path("lessons/week01") or html.parent != student.parent or
                student.suffix != ".ipynb" or html.suffix != ".html" or
                student.stem in registry or html.name in registry.values()):
            raise ValueError("Register each Week 1 student notebook and offline handout once")
        registry[student.stem] = html.name
    if not REQUIRED_PROFILES.keys() <= registry.keys():
        raise ValueError("The Week 1 entry and its three required companions must be registered")
    return registry


def check_reachability(lesson, registry):
    pending = [registry[STEM]]
    visited = set()
    registered = set(registry.values())
    while pending:
        name = pending.pop()
        if name in visited:
            continue
        visited.add(name)
        page = BeautifulSoup((lesson / name).read_text(encoding="utf-8"), "html.parser")
        for a in page.select("main a[href], .week01-navigation a[href]:not([download])"):
            href = urlsplit(a["href"])
            if not href.scheme and not href.netloc and href.path in registered:
                pending.append(href.path)
    if visited != registered:
        raise ValueError(f"Registered handouts unreachable from the Week 1 entry: {sorted(registered - visited)}")


def source_digest(notebook):
    cells = []
    for cell in notebook.cells:
        material = dict(cell)
        for field in ("outputs", "execution_count"):
            material.pop(field, None)
        material["metadata"] = {k: v for k, v in cell.metadata.items() if k != "execution"}
        cells.append(material)
    return hashlib.sha256(json.dumps(cells, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


class OfflineMathRenderer(IPythonRenderer):
    def inline_math(self, body):
        return self._math(body, "inline")

    def block_math(self, body):
        return self._math(body, "block")

    def latex_environment(self, name, body):
        return self.block_math(r"\begin{" + name + "}" + body + r"\end{" + name + "}")

    @staticmethod
    def _math(body, display):
        converted = mathml(body, display=display)
        return converted.replace("<math ", f'<math data-tex="{escape(body, quote=True)}" ', 1)


class OfflineExporter(HTMLExporter):
    @pass_context
    def markdown2html(self, context, source):
        # Use nbconvert's own math-aware parser and attachment handling, including code fences and escapes.
        renderer = OfflineMathRenderer(
            escape=False, attachments=context.get("cell", {}).get("attachments", {}),
            embed_images=self.embed_images, path=context.get("resources", {}).get("metadata", {}).get("path", ""),
            anchor_link_text=self.anchor_link_text, exclude_anchor_links=self.exclude_anchor_links,
            **self.lexer_options)
        return MarkdownWithMath(renderer=renderer).render(source)


def serialized_notebook(notebook):
    stream = StringIO()
    nbformat.write(notebook, stream)
    return stream.getvalue().encode("utf-8")


def verify_download(page, filename, expected_bytes):
    links = page.select(".week01-navigation a[download]")
    if len(links) != 1 or links[0].get("download") != filename:
        raise ValueError(f"{filename}: missing executable notebook download or incorrect filename")
    href = links[0].get("href", "")
    if not href.startswith(NOTEBOOK_DATA_URL):
        raise ValueError(f"{filename}: an offline download must embed the executable notebook")
    try:
        payload = base64.b64decode(href[len(NOTEBOOK_DATA_URL):], validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError(f"{filename}: invalid embedded notebook data") from exc
    if payload != expected_bytes:
        raise ValueError(f"{filename}: downloaded bytes differ from the distributed notebook")


def render(notebook, *, stem=None, lesson=LESSON, download_bytes=None):
    registry = registered_handouts(lesson)
    if stem is None:
        ids = {cell.id for cell in notebook.cells}
        matches = [key for key, (sample, _, _) in REQUIRED_PROFILES.items() if sample in ids]
        if not matches:
            matches = [name for name in registry if source_digest(notebook) ==
                       source_digest(nbformat.read(lesson / (name + ".ipynb"), as_version=4))]
        stem, = matches
    if stem not in registry:
        raise ValueError(f"Unregistered Week 1 student notebook: {stem}")
    notebook_links = {name + ".ipynb": html for name, html in registry.items()}
    title = next(line[2:].strip() for cell in notebook.cells if cell.cell_type == "markdown"
                 for line in cell.source.splitlines() if line.startswith("# "))
    html, _ = OfflineExporter(language_code="ko").from_notebook_node(
        notebook, resources={"metadata": {"name": title}})
    doc = BeautifulSoup(html, "html.parser")
    doc.title.string = title
    for script in doc.head.select("script"):
        script.decompose()
    for anchor in doc.select("main a[href]"):
        href = urlsplit(anchor["href"])
        if not href.scheme and not href.netloc and href.path in notebook_links:
            anchor["href"] = href._replace(path=notebook_links[href.path]).geturl()
    navigation = doc.new_tag("nav", attrs={"class": "week01-navigation", "aria-label": "1주차 학습 자료"})
    if stem != STEM:
        home = doc.new_tag("a", href=registry[STEM])
        home.string = "1주차 통합 교안으로"
        navigation.append(home)
    if download_bytes is None:
        original = lesson / (stem + ".ipynb")
        if original.is_file():
            raw = original.read_bytes()
            if nbformat.reads(raw.decode("utf-8"), as_version=4) == notebook:
                download_bytes = raw
        if download_bytes is None:
            download_bytes = serialized_notebook(notebook)
    elif nbformat.reads(download_bytes.decode("utf-8"), as_version=4) != notebook:
        raise ValueError(f"{stem}: the download and displayed notebook differ")
    payload = base64.b64encode(download_bytes).decode("ascii")
    download = doc.new_tag("a", href=NOTEBOOK_DATA_URL + payload, download=stem + ".ipynb")
    download.string = "실행용 노트북 내려받기 (.ipynb)"
    navigation.append(download)
    doc.main.insert_before(navigation)
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
    for index, image in enumerate(doc.select("main img"), start=1):
        identifier = f"week01-figure-{index}"
        view = doc.new_tag("span", attrs={"class": "week01-figure-view"})
        image.wrap(view)
        frame = doc.new_tag("span", id=identifier, tabindex="0", attrs={
            "class": "week01-figure-scroll", "role": "region", "aria-label": "그림 가로로 살펴보기"})
        image.wrap(frame)
        control = doc.new_tag("input", id=identifier + "-size", type="checkbox", attrs={
            "class": "week01-figure-toggle", "aria-controls": identifier})
        label = doc.new_tag("label", attrs={"for": control["id"], "class": "week01-figure-label"})
        label.string = "그림 원래 크기로 보기"
        frame.insert_before(control)
        frame.insert_before(label)
    return doc


def visible_cells(doc, *, image_bytes):
    cells = []
    for cell in doc.select("main .jp-Cell"):
        content = cell.select_one(".jp-MarkdownOutput, .jp-InputArea-editor pre")
        outputs = cell.select(".jp-OutputArea-output")
        links = [a.get("href") for a in content.select("a[href]")]
        pictures = []
        for image in cell.select(".jp-OutputArea-output img, .jp-MarkdownOutput img"):
            prefix, _, encoded = image["src"].partition(",")
            raw = base64.b64decode(encoded, validate=True)
            if prefix != "data:image/png;base64" or raw[:8] != bytes.fromhex("89504e470d0a1a0a"):
                raise ValueError(f"{cell.get('id')}: expected an embedded PNG")
            if min(struct.unpack(">II", raw[16:24])) < 100:
                raise ValueError(f"{cell.get('id')}: empty or undersized figure")
            pictures.append((image.get("alt"), hashlib.sha256(raw).hexdigest() if image_bytes else None))
        # Adjacent stdout chunks can be grouped differently by kernel transports.
        output = " ".join(" ".join(part.stripped_strings) for part in outputs)
        formulas = [(m.get("data-tex"), str(m)) for m in content.select("math")]
        tables = [[[td.get_text(" ", strip=True) for td in row.select("th, td")] for row in t.select("tr")]
                  for t in cell.select("table")]
        cells.append((cell["id"], content.get_text().strip(), links, " ".join(output.split()), pictures, formulas, tables))
    return cells


def check_plot_correspondence(saved, fresh):
    """Check the painted data and the caption/axis text while tolerating small renderer shifts."""
    def marks(encoded):
        with Image.open(BytesIO(base64.b64decode(encoded))) as picture:
            image = picture.convert("RGB")
            resized = image.resize((240, 160), Image.Resampling.LANCZOS)
            rgb = np.asarray(resized, dtype=int)
            hue = np.asarray(resized.convert("HSV"), dtype=int)[:, :, 0] * 12 // 256
            text = np.asarray(image.resize((500, 300), Image.Resampling.LANCZOS), dtype=int)
        # Most text and axes are neutral. Keep the title and label bands separate from colored data marks.
        ink = (text.max(axis=2) < 150) & (text.max(axis=2) - text.min(axis=2) < 20)
        return rgb.max(axis=2) - rgb.min(axis=2) > 24, hue, (ink[:20], ink[-22:], ink[:, :23], ink[:, -23:])

    def unmatched(mask, hue, reference, ref_hue):
        matched = np.zeros_like(mask)
        for band in np.unique(hue[mask]):
            compatible = reference & (np.minimum((ref_hue - band) % 12, (band - ref_hue) % 12) <= 1)
            close = Image.fromarray(compatible.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(7))
            matched |= (hue == band) & (np.asarray(close) > 0)
        return (mask & ~matched).sum() / mask.sum()

    def label_band_changed(left, right):
        counts = [int(band.sum()) for band in (left, right)]
        if max(counts) < 64:
            return False
        if min(counts) < 0.45 * max(counts):
            return True
        for candidate, reference in ((left, right), (right, left)):
            nearby = Image.fromarray(reference.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(5))
            if (candidate & (np.asarray(nearby) == 0)).sum() > 0.55 * candidate.sum():
                return True
        return False

    for old, new in zip(saved.cells, fresh.cells):
        old_images = [o.data["image/png"] for o in old.get("outputs", []) if "image/png" in o.get("data", {})]
        new_images = [o.data["image/png"] for o in new.get("outputs", []) if "image/png" in o.get("data", {})]
        if len(old_images) != len(new_images):
            raise ValueError(f"{old.id}: the number of freshly executed plots changed")
        for left, right in zip(old_images, new_images):
            if left == right:
                continue
            (a, a_hue, a_labels), (b, b_hue, b_labels) = marks(left), marks(right)
            if not a.any() or not b.any():
                raise ValueError(f"{old.id}: the fresh or saved plot lost its colored data marks")
            # A small spatial and hue tolerance accommodates differences in tight bounding boxes and antialiasing.
            mismatch = max(unmatched(a, a_hue, b, b_hue), unmatched(b, b_hue, a, a_hue))
            if mismatch > 0.08 or abs(int(a.sum()) - int(b.sum())) / max(a.sum(), b.sum()) > 0.15:
                raise ValueError(f"{old.id}: freshly rendered data marks differ from the saved plot")
            if any(label_band_changed(x, y) for x, y in zip(a_labels, b_labels)):
                raise ValueError(f"{old.id}: freshly rendered title or axis labels differ from the saved plot")


def has_anchor(doc, fragment):
    return any(doc.find(id=value) for value in (fragment, unquote(fragment)))


def check_links(doc, lesson):
    local = set()
    targets = {}
    for anchor in doc.select(".week01-navigation a[href]:not([download]), main a[href]"):
        href = urlsplit(anchor["href"])
        if href.scheme or href.netloc:
            continue
        if href.path:
            relative = unquote(href.path)
            path = lesson / relative
            if not path.is_file():
                raise ValueError(f"Missing lesson resource: {relative}")
            local.add(relative)
            if href.fragment and path.suffix == ".html":
                if path not in targets:
                    targets[path] = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
                if not has_anchor(targets[path], href.fragment):
                    raise ValueError(f"Missing destination anchor: {relative}#{href.fragment}")
        elif href.fragment and not has_anchor(doc, href.fragment):
            raise ValueError(f"Missing page anchor: {href.fragment}")
    return sorted(local)


def verify(source, fresh, published, *, stem=STEM, lesson=LESSON):
    nbformat.validate(source)
    nbformat.validate(fresh)
    registry = registered_handouts(lesson)
    expected_answers = ANSWERS.get(stem, set())
    authored = source_digest(source)
    if authored != source_digest(fresh):
        raise ValueError("Execution changed the authored cells")
    for book in (source, fresh):
        code = [c for c in book.cells if c.cell_type == "code"]
        if [c.execution_count for c in code] != list(range(1, len(code) + 1)):
            raise ValueError(f"{stem}: code cells were not all run in order")
        if not expected_answers.issubset(c.id for c in code):
            raise ValueError(f"{stem}: an expected independent answer cell is missing")
        for cell in code:
            if any(o.output_type == "error" or o.get("name") == "stderr" for o in cell.outputs):
                raise ValueError(f"{cell.id}: inspect kernel error or warning output")
            independent = cell.id in expected_answers or "student-code" in cell.metadata.get("tags", [])
            has_code = any(line.strip() and not line.lstrip().startswith("#") for line in cell.source.splitlines())
            if (independent and has_code) or (not has_code and cell.outputs):
                raise ValueError(f"{cell.id}: keep the independent student answer blank")
    doc = render(fresh, stem=stem, lesson=lesson)
    committed = BeautifulSoup(published, "html.parser")
    for page in (doc, committed):
        if page.select("script[src], link[rel=stylesheet][href]"):
            raise ValueError(f"{stem}: offline handout requires an external script or stylesheet")
        for picture in page.select("main img"):
            frame = picture.find_parent(class_="week01-figure-scroll")
            toggle = frame and frame.find_previous_sibling("input", class_="week01-figure-toggle")
            label = toggle and page.find("label", attrs={"for": toggle.get("id")})
            if (not toggle or not label or not label.get_text(strip=True) or
                    toggle.get("aria-controls") != frame.get("id") or frame.get("tabindex") != "0"):
                raise ValueError("Missing keyboard-accessible full-size figure control")
        meta = page.select_one('meta[name="koai-notebook-source-sha256"]')
        if (page.html.get("lang") != "ko" or page.title.get_text() != doc.title.get_text()
                or not meta or meta.get("content") != authored):
            raise ValueError("HTML language, title or authored-source fingerprint is stale")
    style = committed.find("style", id="week01-reading-layout")
    if not style or style.string != READING_CSS:
        raise ValueError("Published reading layout differs from the current export")
    if visible_cells(render(source, stem=stem, lesson=lesson), image_bytes=True) != visible_cells(committed, image_bytes=True):
        raise ValueError("Published HTML differs from the notebook's saved cells, outputs, links or PNGs")
    if visible_cells(doc, image_bytes=False) != visible_cells(committed, image_bytes=False):
        raise ValueError("Fresh execution differs from the published cells, text, tables or figure descriptions")
    check_plot_correspondence(source, fresh)
    notebook_path = lesson / (stem + ".ipynb")
    verify_download(committed, notebook_path.name, notebook_path.read_bytes())
    figures = doc.select(".jp-OutputArea-output img")
    tables = doc.select(".jp-OutputArea-output table")
    _, minimum_figures, minimum_tables = REQUIRED_PROFILES.get(stem, (None, 0, 0))
    if len(figures) < minimum_figures or len(tables) < minimum_tables:
        raise ValueError(f"{stem}: expected at least {minimum_figures} worked plots and {minimum_tables} output tables")
    attached = sum(len(c.get("attachments", {})) for c in source.cells)
    if len(doc.select(".jp-MarkdownOutput img")) < attached:
        raise ValueError(f"{stem}: an attached lesson diagram is missing")
    links = check_links(committed, lesson)
    nav = [a["href"] for a in committed.select(".week01-navigation a[href]:not([download])")]
    if stem != STEM and registry[STEM] not in nav:
        raise ValueError("A companion handout has no route back to the integrated lesson")
    if stem == STEM:
        missing = {registry[name] for name in REQUIRED_PROFILES if name != STEM} - set(links)
        if missing:
            raise ValueError(f"Integrated handout is missing offline companions: {sorted(missing)}")
        plan = BeautifulSoup((ROOT / "curriculum/student-plan.html").read_text(), "html.parser")
        entry = "https://github.com/jlee-ax/AI-Olympiad/blob/main/lessons/week01/" + STEM + ".ipynb"
        if [a["href"] for a in plan.select('#week-1 a[href$=".ipynb"]')] != [entry]:
            raise ValueError("The student plan must open the maintained Week 1 notebook")
    return {"notebook": stem, "authored_cells_sha256": authored, "code_cells": len(code),
            "figures": len(figures), "output_tables": len(tables), "math": len(doc.select("math")),
            "attached_diagrams": attached, "local_resources": links}


def browser_check(path, executable):
    from playwright.sync_api import sync_playwright

    registry = registered_handouts(path.parent)
    stem, = (name for name, html in registry.items() if html == path.name)
    notebook = path.parent / (stem + ".ipynb")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=executable or None)
        directions = set()
        for width in (1280, 390):
            page = browser.new_page(viewport={"width": width, "height": 850}, accept_downloads=True)
            page.route("http://**/*", lambda route: route.abort())
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
            if not page.locator("main table").evaluate_all("""tables => tables.every(table => {
                const row = table.querySelector('tr');
                if (!row || table.getBoundingClientRect().width < 1) return false;
                return [row.firstElementChild, row.lastElementChild].every(cell => {
                    if (!cell) return false;
                    cell.scrollIntoView({block: 'nearest', inline: 'nearest'});
                    const r = cell.getBoundingClientRect();
                    return r.height > 0 && r.width > 0 && r.right > 0 && r.left < innerWidth;
                });
            })"""):
                raise ValueError(f"A table column cannot be reached at {width}px")
            for figure in page.locator("main img, main math").all():
                figure.scroll_into_view_if_needed()
                if not figure.evaluate("""node => node.getBoundingClientRect().width > 0 &&
                      (node.tagName.toLowerCase() === 'math' ? node.namespaceURI === 'http://www.w3.org/1998/Math/MathML'
                       : node.complete && node.naturalWidth > 0 && node.alt.trim().length > 0)"""):
                    raise ValueError(f"A diagram, plot or formula did not display at {width}px")
            if width == 390:
                for toggle in page.locator(".week01-figure-toggle").all():
                    toggle.check()
                    if not toggle.evaluate("""node => {
                        const frame = document.getElementById(node.getAttribute('aria-controls'));
                        const image = frame.querySelector('img');
                        frame.scrollLeft = frame.scrollWidth;
                        return image.getBoundingClientRect().width + 1 >= image.naturalWidth
                            && (frame.scrollWidth <= frame.clientWidth + 1 || frame.scrollLeft > 0)
                            && document.documentElement.scrollWidth <= innerWidth + 1;
                    }"""):
                        raise ValueError("The full-size figure cannot be inspected on a narrow screen")
                    toggle.uncheck()
            with page.expect_download() as triggered:
                page.locator(".week01-navigation a[download]").click()
            download = triggered.value
            if (download.suggested_filename != notebook.name or download.failure()
                    or Path(download.path()).read_bytes() != notebook.read_bytes()):
                raise ValueError(f"{path.name}: the executable download does not match the notebook")
            urls = page.locator(".week01-navigation a[href]:not([download]), main a[href]").evaluate_all(
                "anchors => anchors.map(a => a.getAttribute('href'))")
            for url in dict.fromkeys(urls):
                target = urlsplit(url)
                if target.path not in registry.values():
                    continue
                page.locator(f"a[href={json.dumps(url, ensure_ascii=False)}]").first.click()
                expected_url = (path.parent.resolve() / target.path).as_uri()
                if target.fragment:
                    expected_url += "#" + target.fragment
                page.wait_for_url(expected_url, wait_until="load")
                arrived = urlsplit(page.url)
                if (Path(unquote(arrived.path)) != path.parent.resolve() / target.path
                        or unquote(arrived.fragment) != unquote(target.fragment)):
                    raise ValueError(f"{path.name}: failed to navigate to {url}")
                if target.fragment and not page.evaluate("""key => Boolean(document.getElementById(key)
                            || document.getElementById(decodeURIComponent(key)))""", target.fragment):
                    raise ValueError(f"{path.name}: linked section did not open: {url}")
                page.locator("h1").wait_for()
                directions.add(url)
                page.goto(path.resolve().as_uri(), wait_until="load")
            page.close()
        browser.close()
    return sorted(directions)


def write_fresh_edition(notebook, stem, output_dir, *, lesson=LESSON):
    html = registered_handouts(lesson)[stem]
    filename = stem + ".ipynb"
    raw = serialized_notebook(notebook)
    page = render(notebook, stem=stem, lesson=lesson, download_bytes=raw)
    (output_dir / filename).write_bytes(raw)
    (output_dir / html).write_text(str(page), encoding="utf-8")
    verify_download(page, filename, (output_dir / filename).read_bytes())


def checked_execution(stem, output_dir, browser):
    path = LESSON / (stem + ".ipynb")
    source = nbformat.read(path, as_version=4)
    blank = copy.deepcopy(source)
    for cell in blank.cells:
        if cell.cell_type == "code":
            cell.outputs, cell.execution_count = [], None
            cell.metadata.pop("execution", None)
    with tempfile.TemporaryDirectory(prefix=stem + "-") as temporary:
        root = Path(temporary)
        directory = root / "lesson"
        scratch = root / "scratch"
        directory.mkdir()
        scratch.mkdir()
        inputs = [path, *LESSON.rglob("*.csv")]
        for item in inputs:
            dest = directory / item.relative_to(LESSON)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(item, dest)
        fresh = NotebookClient(blank, kernel_name="python3", timeout=120, allow_errors=False,
                               record_timing=False).execute(cwd=str(directory), env={**os.environ, "TMPDIR": str(scratch)})
        contents = {p.relative_to(directory) for p in directory.rglob("*") if p.is_file()}
        if (contents != {p.relative_to(LESSON) for p in inputs}
                or any(p.read_bytes() != (directory / p.relative_to(LESSON)).read_bytes() for p in inputs)
                or any(scratch.rglob("*.zip"))):
            raise ValueError(f"{stem}: the notebook modified an input or left an unexpected file or ZIP")
    html = LESSON / registered_handouts(LESSON)[stem]
    receipt = verify(source, fresh, html.read_text(encoding="utf-8"), stem=stem)
    if output_dir:
        write_fresh_edition(fresh, stem, output_dir)
    if browser is not None:
        receipt["browser_directions"] = browser_check(html, browser)
        receipt["browser_widths"] = [1280, 390]
    return receipt


def main():
    registry = registered_handouts(LESSON)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notebook", action="append", choices=registry, help="Limit execution to named notebooks")
    parser.add_argument("--output-dir", type=Path, help="Save fresh executions, HTML and local CSV data here")
    parser.add_argument("--browser", nargs="?", const="", metavar="EXECUTABLE",
                        help="Check all local reading links and downloads in Playwright Chromium")
    args = parser.parse_args()
    from matplotlib import font_manager
    font_manager.findfont(font_manager.FontProperties())
    os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")
    if args.output_dir:
        if args.output_dir.resolve().is_relative_to(LESSON.resolve()):
            parser.error("Use a separate output directory to preserve published materials")
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for csv in LESSON.rglob("*.csv"):
            dest = args.output_dir / csv.relative_to(LESSON)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(csv, dest)
    if not args.notebook:
        check_reachability(LESSON, registry)
    receipts = [checked_execution(stem, args.output_dir, args.browser) for stem in dict.fromkeys(args.notebook or registry)]
    print(json.dumps(receipts, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
