# Week 1 student notebooks and offline handouts

Four independent clean-kernel runs executed all 93 code cells in the 224 student cells. Each run began with cleared outputs, in its own lesson directory with copies of the distributed CSV files. Cell counts run consecutively from 1 in each notebook. The complete authored notebook objects, including metadata, Markdown attachments and cell IDs, matched their frozen manuscripts after removing code outputs and execution counts. All 15 independent answer cells remain blank. No execution produced a cell error, stderr output, modified input or leftover submission ZIP.

| Student material | Cells / code | Blank answers | Output tables | Worked plots / attached diagrams | Executed notebook SHA-256 prefix | Offline HTML SHA-256 prefix |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| Integrated lesson | 57 / 28 | 5 | 5 | 2 / 0 | `f11eb1463bef` | `14e7633a9c65` |
| Python and tables | 98 / 33 | 6 | 12 | 5 / 2 | `424835eaff77` | `10f6a1e701ac` |
| Axes and linear algebra | 35 / 16 | 2 | 0 | 0 / 0 | `dc476a122fc1` | `b0b72f87d003` |
| Problem-to-submission pipeline | 34 / 16 | 2 | 6 | 0 / 0 | `ef54282eaec5` | `a610e51404a9` |

The equivalent run on the immutable starting commit `80033e4e3c83114a408c6e701113a879c632394d` executed 87 code cells. The original tables notebook contained no saved outputs, though its HTML showed five plotted outputs and eleven output tables. The three companion pages declared English and loaded external scripts. Two used the generic title “Notebook.” The tables companion's mathematical notation depended on an external renderer.

## Reading, navigation and visual checks

The current HTML preserves its Korean title and language, embeds each PNG with a Korean description, and typesets all 107 authored formulas as native MathML. Two formulas retain matrix rows and columns. The source comparison checks actual cell text, links, table cells, mathematical markup, image descriptions and embedded PNG bytes against the saved notebook. Fresh plot checks compare the locations and hues of data marks and allow small differences from font-dependent rasterization.

The integrated handout reaches all three companions. The four pages contain 8, 4, 6 and 3 distinct Week 1 reading destinations respectively, counted per originating page. Every local destination file and named HTML section resolved. Inter-book reading links open the registered sibling HTML handout at the original section. Each page separately offers its matching executable notebook. The whole-set check derives filenames from the registered release and tests reachability from the integrated lesson.

Visual inspection used the actual opening cell and one instructional detail from each exported page at 1280px and 390px, rendered offline with WeasyPrint and Poppler. The detail views covered the integrated scatterplot, the tables companion's paired scatterplot, the bridge's score-axis table and the pipeline's keyed validation table. Both sides of the paired plot fit on a phone, but the fitted labels were too small to read comfortably. A labeled keyboard-operable control now displays the same embedded image at original size in a horizontally scrollable region. Two additional 390px raster views confirmed original-size point IDs, plot axes and the legend.

## Execution and regression evidence

The source-bound tables validator passed both its ordinary CSV run and its standalone fallback, including tests against functions read from the published teacher guide. The pipeline validator passed all 18 named check groups, including reopening the real temporary ZIP, parsing the actual validation file and rejecting a teacher audit CSV with reversed predictions. The integrated transfer and cross-book route checkers also passed.

Twelve delivery regression tests ran against the public handouts. Faults included a missing sibling fragment, a different real plot in matching saved notebook and HTML, recolored marks in the correct positions, a removed matrix, an unwired figure control, a filled bridge answer and a stale ZIP member. The positive controls accepted a 3-by-2-pixel renderer shift and exercised a temporary fifth registered student notebook with a separately named handout. Its unreachable state failed, and its real authored incoming link made it reachable.

Local runs used Python 3.12, ipykernel 7.4.0, nbconvert 7.17.2, NumPy 2.3.5, pandas 2.2.3, Matplotlib 3.10.8, Seaborn 0.13.2, scikit-learn 1.8.0 and latex2mathml 3.81.1. Each local kernel ran in its own Python process with IPython's in-process transport. The host denied socket creation for ordinary Jupyter transport and the full Chrome application.

## File-origin notebook downloads

The first main-branch job for this bundle failed while waiting for Chromium's notebook download event. Local Chromium independently reproduced the preceding handout at 1280px and 390px. Clicking the relative download link navigated to the sibling notebook JSON at both sizes. [First hosted job and failing browser step](https://github.com/jlee-ax/AI-Olympiad/actions/runs/44733965949/job/136280551091)

Each corrected handout embeds its own original notebook bytes in a native download link with the exact filename. The four pages together grew by 952,451 bytes. The largest handout is 1,512,502 bytes. The independent check preserves original JSON formatting and trailing newlines and rejects another valid notebook, malformed encoding, the old relative link and an incorrect filename. A fresh preview embeds the bytes it actually writes alongside its rendered page. The prior handouts' visible cells, image bytes and ordinary reading links matched the corrected editions.

A standalone headless Chromium 152.0.7977.0 ran the same Playwright checks locally against all four installed pages opened through `file://`, with external HTTP requests blocked. The eight real download events delivered the expected filenames and exact notebook bytes. At each width, the browser followed all 21 per-origin reading destinations, checked their sections and reached both ends of each student table. It displayed the native mathematics and exercised original-size figures at 390px. The main-branch workflow independently repeats those checks with its own Chromium build and conventional Jupyter kernels.
