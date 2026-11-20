# Week 1 student notebooks and offline handouts

Four independent clean-kernel runs executed all 93 code cells in the 224 student cells. Each run began with cleared outputs, in its own lesson directory with copies of the distributed CSV files. Cell counts run consecutively from 1 in each notebook. The complete authored notebook objects, including metadata, Markdown attachments and cell IDs, matched their frozen manuscripts after removing code outputs and execution counts. All 15 independent answer cells remain blank. No execution produced a cell error, stderr output, modified input or leftover submission ZIP.

| Student material | Cells / code | Blank answers | Output tables | Worked plots / attached diagrams | Executed notebook SHA-256 prefix | Offline HTML SHA-256 prefix |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| Integrated lesson | 57 / 28 | 5 | 5 | 2 / 0 | `f11eb1463bef` | `e0ae9aac8ec0` |
| Python and tables | 98 / 33 | 6 | 12 | 5 / 2 | `424835eaff77` | `c873afd32820` |
| Axes and linear algebra | 35 / 16 | 2 | 0 | 0 / 0 | `dc476a122fc1` | `3f8a815b8b2b` |
| Problem-to-submission pipeline | 34 / 16 | 2 | 6 | 0 / 0 | `ef54282eaec5` | `d029135c4668` |

The equivalent run on the immutable starting commit `80033e4e3c83114a408c6e701113a879c632394d` executed 87 code cells. The original tables notebook contained no saved outputs, though its HTML showed five plotted outputs and eleven output tables. The three companion pages declared English and loaded external scripts. Two used the generic title “Notebook.” The tables companion's mathematical notation depended on an external renderer.

## Reading, navigation and visual checks

The current HTML preserves its Korean title and language, embeds each PNG with a Korean description, and typesets all 107 authored formulas as native MathML. Two formulas retain matrix rows and columns. The source comparison checks actual cell text, links, table cells, mathematical markup, image descriptions and embedded PNG bytes against the saved notebook. Fresh plot checks compare the locations and hues of data marks and allow small differences from font-dependent rasterization.

The integrated handout reaches all three companions. The four pages contain 8, 4, 6 and 3 distinct Week 1 reading destinations respectively, counted per originating page. Every local destination file and named HTML section resolved. Inter-book reading links open the registered sibling HTML handout at the original section. Each page separately offers its matching executable notebook. The whole-set check derives filenames from the registered release and tests reachability from the integrated lesson.

Visual inspection used the actual opening cell and one instructional detail from each exported page at 1280px and 390px, rendered offline with WeasyPrint and Poppler. The detail views covered the integrated scatterplot, the tables companion's paired scatterplot, the bridge's score-axis table and the pipeline's keyed validation table. Both sides of the paired plot fit on a phone, but the fitted labels were too small to read comfortably. A labeled keyboard-operable control now displays the same embedded image at original size in a horizontally scrollable region. Two additional 390px raster views confirmed original-size point IDs, plot axes and the legend.

## Execution and regression evidence

The source-bound tables validator passed both its ordinary CSV run and its standalone fallback, including tests against functions read from the published teacher guide. The pipeline validator passed all 18 named check groups, including reopening the real temporary ZIP, parsing the actual validation file and rejecting a teacher audit CSV with reversed predictions. The integrated transfer and cross-book route checkers also passed.

Nine delivery regression tests ran against the public handouts. Faults included a missing sibling fragment, a different real plot in matching saved notebook and HTML, recolored marks in the correct positions, a removed matrix, an unwired figure control, a filled bridge answer and a stale ZIP member. The positive controls accepted a 3-by-2-pixel renderer shift and exercised a temporary fifth registered student notebook with a separately named handout. Its unreachable state failed, and its real authored incoming link made it reachable.

Local runs used Python 3.12, ipykernel 7.4.0, nbconvert 7.17.2, NumPy 2.3.5, pandas 2.2.3, Matplotlib 3.10.8, Seaborn 0.13.2, scikit-learn 1.8.0 and latex2mathml 3.81.1. Each local kernel ran in its own Python process with IPython's in-process transport. The host denied socket creation for ordinary Jupyter transport and Chromium. The main-branch Week 1 workflow runs separate conventional Jupyter kernels and Chromium at both screen sizes. Its browser checks open real reading links, verify the bytes downloaded from every notebook control, reach both ends of tables, and exercise actual-size figures with external HTTP requests blocked.
