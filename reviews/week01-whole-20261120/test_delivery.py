"""Fault controls on the published Week 1 inputs and handouts. No checkout files are changed."""
import base64
import copy
from io import BytesIO
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

from bs4 import BeautifulSoup
import nbformat
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import check_week01_render as delivery


def notebook(stem):
    return nbformat.read(delivery.LESSON / (stem + ".ipynb"), as_version=4)


def picture(book, cell_id):
    cell = next(c for c in book.cells if c.id == cell_id)
    return next(o.data for o in cell.outputs if "image/png" in o.get("data", {}))


class DeliveryFaults(unittest.TestCase):
    def test_every_published_download_contains_the_exact_named_file(self):
        for stem, html in delivery.registered_handouts(delivery.LESSON).items():
            with self.subTest(stem=stem):
                filename = stem + ".ipynb"
                page = BeautifulSoup((delivery.LESSON / html).read_text(), "html.parser")
                link, = page.select(".week01-navigation a[download]")
                self.assertEqual(link["download"], filename)
                media, encoded = link["href"].split(",", 1)
                self.assertEqual(media, "data:application/octet-stream;base64")
                self.assertEqual(base64.b64decode(encoded, validate=True), (delivery.LESSON / filename).read_bytes())

    def test_download_detects_the_relative_link_wrong_filename_and_corrupt_bytes(self):
        filename = "week01_integrated.ipynb"
        page = BeautifulSoup((delivery.LESSON / "week01_integrated.html").read_text(), "html.parser")
        link = page.select_one(".week01-navigation a[download]")
        raw = (delivery.LESSON / filename).read_bytes()
        other = (delivery.LESSON / "week01_problem_pipeline.ipynb").read_bytes()
        url = delivery.NOTEBOOK_DATA_URL
        for title, href, name, error in [
            ("sibling file", filename, filename, "must embed"),
            ("wrong name", link["href"], "another.ipynb", "incorrect filename"),
            ("damaged encoding", url + "invalid!!", filename, "invalid embedded"),
            ("wrong real book", url + base64.b64encode(other).decode(), filename, "bytes differ"),
            ("same parsed notebook, missing final newline", url + base64.b64encode(raw.rstrip()).decode(),
             filename, "bytes differ"),
        ]:
            with self.subTest(title=title):
                link["href"], link["download"] = href, name
                with self.assertRaisesRegex(ValueError, error):
                    delivery.verify_download(page, filename, raw)

    def test_render_preserves_original_file_bytes_and_stages_the_actual_fresh_capture(self):
        stem = "week01_problem_pipeline"
        filename = stem + ".ipynb"
        saved = notebook(stem)
        differently_formatted = (json.dumps(json.loads((delivery.LESSON / filename).read_bytes()),
                                            ensure_ascii=False, indent=3) + "\n").encode()
        page = delivery.render(saved, stem=stem, download_bytes=differently_formatted)
        delivery.verify_download(page, filename, differently_formatted)
        fresh = copy.deepcopy(saved)
        stdout = next(o for cell in fresh.cells for o in cell.get("outputs", []) if o.get("name") == "stdout")
        stdout.text += "changed output in this staged execution\n"
        with self.assertRaisesRegex(ValueError, "displayed notebook differ"):
            delivery.render(fresh, stem=stem, download_bytes=differently_formatted)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            shutil.copyfile(delivery.LESSON / "lesson-manifest.json", output / "lesson-manifest.json")
            (output / filename).write_bytes(differently_formatted)
            original = delivery.render(saved, stem=stem, lesson=output)
            delivery.verify_download(original, filename, differently_formatted)
            delivery.write_fresh_edition(fresh, stem, output)
            fresh_bytes = (output / filename).read_bytes()
            self.assertEqual(nbformat.reads(fresh_bytes.decode(), as_version=4), fresh)
            self.assertNotEqual(fresh_bytes, (delivery.LESSON / filename).read_bytes())
            page = BeautifulSoup((output / (stem + ".html")).read_text(), "html.parser")
            delivery.verify_download(page, filename, fresh_bytes)

    def test_new_registered_companion_uses_its_declared_handout_and_remains_reachable(self):
        with tempfile.TemporaryDirectory() as folder:
            lesson = Path(folder)
            manifest = json.loads((delivery.LESSON / "lesson-manifest.json").read_text())
            members = manifest["current_release"]["members"]
            for member in members.values():
                html = Path(member["html"]).name
                shutil.copyfile(delivery.LESSON / html, lesson / html)
            stem = "week01_extra_practice"
            html = "extra-reading.html"
            members["extra"] = {"student": "lessons/week01/" + stem + ".ipynb",
                                "html": "lessons/week01/" + html}
            (lesson / "lesson-manifest.json").write_text(json.dumps(manifest))
            fresh = nbformat.v4.new_notebook(cells=[
                nbformat.v4.new_markdown_cell("# 추가 연습\n\n[통합 교안](week01_integrated.ipynb#week01-check)"),
                nbformat.v4.new_code_cell("# 답을 여기에 작성하세요.", execution_count=1,
                                         metadata={"tags": ["student-code"]})])
            nbformat.write(fresh, lesson / (stem + ".ipynb"))
            page = str(delivery.render(fresh, stem=stem, lesson=lesson))
            (lesson / html).write_text(page)
            self.assertEqual(delivery.verify(fresh, fresh, page, stem=stem, lesson=lesson)["code_cells"], 1)
            registry = delivery.registered_handouts(lesson)
            self.assertEqual(registry[stem], html)
            with self.assertRaisesRegex(ValueError, "unreachable"):
                delivery.check_reachability(lesson, registry)
            core = notebook(delivery.STEM)
            core.cells[0].source += f"\n\n[추가 연습]({stem}.ipynb)"
            (lesson / registry[delivery.STEM]).write_text(str(delivery.render(core, stem=delivery.STEM, lesson=lesson)))
            delivery.check_reachability(lesson, registry)

    def test_integrated_rejects_a_missing_section_in_an_existing_companion(self):
        stem = "week01_integrated"
        page = BeautifulSoup((delivery.LESSON / (stem + ".html")).read_text(), "html.parser")
        link = next(a for a in page.select("main a[href]") if a["href"].startswith("week01_problem_pipeline.html"))
        delivery.check_links(page, delivery.LESSON)
        link["href"] = "week01_problem_pipeline.html#missing-submission-section"
        with self.assertRaisesRegex(ValueError, "Missing destination anchor"):
            delivery.check_links(page, delivery.LESSON)

    def test_tables_feature_landing_displays_the_actual_named_digit_rows(self):
        from sklearn.datasets import load_digits

        page = BeautifulSoup((delivery.LESSON / "week01_python_tables.html").read_text(), "html.parser")
        landing = page.find(id="cell-id=3468f4e4")
        self.assertIsNotNone(landing)
        table = landing.select_one(".jp-OutputArea-output table")
        self.assertIsNotNone(table, "The direct feature lesson must display the digit rows as a table.")
        fields = ["pixel_4_4", "pixel_2_3", "target"]
        self.assertEqual([c.get_text(strip=True) for c in table.select("thead tr:first-child th")],
                         ["", *fields])
        observed = []
        for row in table.select("tbody tr"):
            index = row.find("th", recursive=False)
            self.assertIsNotNone(index, "A row header must identify the original digit sample.")
            observed.append((int(index.get_text()), [float(c.get_text()) for c in row.find_all("td", recursive=False)]))
        digits = load_digits(as_frame=True).frame
        expected = [(i, digits.loc[i, fields].tolist()) for i in [7, 2, 11]]
        self.assertEqual(observed, expected)

    def test_tables_rejects_a_real_histogram_substituted_for_the_scatter_plot(self):
        stem = "week01_python_tables"
        fresh = notebook(stem)
        stale = copy.deepcopy(fresh)
        picture(stale, "48d931b0")["image/png"] = picture(fresh, "8d3421bb")["image/png"]
        # Both the saved notebook and its HTML now contain the same authentic but wrong PNG.
        page = str(delivery.render(stale, stem=stem))
        with self.assertRaisesRegex(ValueError, "freshly rendered data marks differ"):
            delivery.verify(stale, fresh, page, stem=stem)

    def test_tables_rejects_a_real_wrong_title_with_unchanged_colored_marks(self):
        fresh = notebook("week01_python_tables")
        stale = copy.deepcopy(fresh)
        target = picture(stale, "48d931b0")
        original = Image.open(BytesIO(base64.b64decode(target["image/png"]))).convert("RGB")
        other = Image.open(BytesIO(base64.b64decode(picture(fresh, "8d3421bb")["image/png"]))).convert("L")
        # The worked histogram supplies a real but incorrect headline for the paired scatterplot.
        title = other.crop((0, 0, other.width, round(other.height * 0.06)))
        wrong = original.copy()
        wrong.paste(title.resize((wrong.width, round(wrong.height * 0.06)), Image.Resampling.LANCZOS), (0, 0))
        self.assertEqual(original.convert("HSV").getchannel("S").tobytes(),
                         wrong.convert("HSV").getchannel("S").tobytes())
        output = BytesIO()
        wrong.save(output, format="PNG")
        target["image/png"] = base64.b64encode(output.getvalue()).decode("ascii")
        with self.assertRaisesRegex(ValueError, "title or axis labels differ"):
            delivery.check_plot_correspondence(stale, fresh)

    def test_tables_accepts_a_small_renderer_shift(self):
        saved = notebook("week01_python_tables")
        shifted = copy.deepcopy(saved)
        data = picture(shifted, "48d931b0")
        with Image.open(BytesIO(base64.b64decode(data["image/png"]))) as original:
            canvas = Image.new("RGB", original.size, "white")
            canvas.paste(original, (3, 2))
            output = BytesIO()
            canvas.save(output, format="PNG")
        data["image/png"] = base64.b64encode(output.getvalue()).decode("ascii")
        delivery.check_plot_correspondence(saved, shifted)

    def test_tables_rejects_recolored_figure_marks_in_the_same_positions(self):
        saved = notebook("week01_python_tables")
        recolored = copy.deepcopy(saved)
        data = picture(recolored, "48d931b0")
        with Image.open(BytesIO(base64.b64decode(data["image/png"]))) as original:
            red, green, blue = original.convert("RGB").split()
            output = BytesIO()
            Image.merge("RGB", (green, blue, red)).save(output, format="PNG")
        data["image/png"] = base64.b64encode(output.getvalue()).decode("ascii")
        with self.assertRaisesRegex(ValueError, "freshly rendered data marks differ"):
            delivery.check_plot_correspondence(saved, recolored)

    def test_tables_rejects_a_figure_with_an_unwired_enlargement_control(self):
        stem = "week01_python_tables"
        book = notebook(stem)
        page = BeautifulSoup((delivery.LESSON / (stem + ".html")).read_text(), "html.parser")
        toggle = page.select_one(".week01-figure-toggle")
        self.assertIsNotNone(toggle)
        toggle["aria-controls"] = "no-such-figure"
        with self.assertRaisesRegex(ValueError, "full-size figure control"):
            delivery.verify(book, book, str(page), stem=stem)

    def test_tables_rejects_a_formula_removed_from_an_offline_handout(self):
        stem = "week01_python_tables"
        book = notebook(stem)
        page = BeautifulSoup((delivery.LESSON / (stem + ".html")).read_text(), "html.parser")
        matrix = page.select_one("main math:has(mtable)")
        self.assertIsNotNone(matrix)
        matrix.decompose()
        with self.assertRaisesRegex(ValueError, "Published HTML differs"):
            delivery.verify(book, book, str(page), stem=stem)

    def test_bridge_rejects_a_published_answer_even_with_matching_fresh_content(self):
        stem = "week01_axes_linear_bridge"
        filled = notebook(stem)
        answer = next(cell for cell in filled.cells if cell.id == "7b96a39e")
        answer.source = "print([0, 1, 2])"
        answer.outputs = [nbformat.v4.new_output("stream", name="stdout", text="[0, 1, 2]\n")]
        with self.assertRaisesRegex(ValueError, "independent student answer blank"):
            delivery.verify(filled, filled, str(delivery.render(filled, stem=stem)), stem=stem)

    def test_pipeline_rejects_a_stale_zip_member_name_in_both_editions(self):
        stem = "week01_problem_pipeline"
        fresh = notebook(stem)
        stale = copy.deepcopy(fresh)
        output = next(o for c in stale.cells for o in c.get("outputs", [])
                      if o.get("name") == "stdout" and "submissionA.csv" in o.text)
        output.text = output.text.replace("submissionA.csv", "submissionB.csv", 1)
        page = str(delivery.render(stale, stem=stem))
        with self.assertRaisesRegex(ValueError, "Fresh execution differs"):
            delivery.verify(stale, fresh, page, stem=stem)


if __name__ == "__main__":
    unittest.main()
