"""
Build reports/Risk Report.pdf from reports/Risk Report.md.

Uses the `markdown` library to render the markdown to HTML (with table
support), wraps in a CSS stylesheet aimed at a business-document
aesthetic, then renders to PDF with `xhtml2pdf` — chosen because it is
pure Python with no native library dependencies, so it works
identically on Windows, macOS and Linux.

Run:
    python build_risk_report_pdf.py

Quality note: xhtml2pdf uses ReportLab under the hood. CSS support is a
useful subset rather than the full spec (no flexbox, limited
positioning), but it handles headings, tables, lists, code blocks and
images cleanly, which covers every construct in Risk Report.md.
"""
from pathlib import Path
import sys

import markdown
from xhtml2pdf import pisa

REPO_ROOT  = Path(__file__).parent.resolve()
INPUT_MD   = REPO_ROOT / "reports" / "Risk Report.md"
OUTPUT_PDF = REPO_ROOT / "reports" / "Risk Report.pdf"

assert INPUT_MD.exists(), f"Input not found: {INPUT_MD}"
md_text = INPUT_MD.read_text(encoding="utf-8")

# Rewrite relative image paths (figures/foo.png) to absolute paths so
# xhtml2pdf can resolve them regardless of the working directory the
# user runs the script from.
figures_abs = (INPUT_MD.parent / "figures").as_posix()
md_text = md_text.replace("](figures/", f"]({figures_abs}/")

# Markdown -> HTML body
html_body = markdown.markdown(
    md_text,
    extensions=["tables", "fenced_code", "sane_lists"],
    output_format="html5",
)

# Full HTML document. The @page rule + the page-number trick are
# xhtml2pdf-flavoured (uses pdf:pagenumber / pdf:pagecount tags).
html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Financial Portfolio Risk Analysis</title>
<style>
@page {{
    size: a4 portrait;
    margin: 22mm 18mm 22mm 18mm;

    @frame header_frame {{
        -pdf-frame-content: header_content;
        left: 18mm; right: 18mm; top: 10mm; height: 8mm;
    }}
    @frame footer_frame {{
        -pdf-frame-content: footer_content;
        left: 18mm; right: 18mm; bottom: 10mm; height: 8mm;
    }}
}}

body {{
    font-family: "Helvetica", "Arial", sans-serif;
    font-size: 10.5pt;
    line-height: 1.45;
    color: #1a1a1a;
}}

/* Title */
h1 {{
    font-family: "Helvetica", "Arial", sans-serif;
    font-size: 22pt;
    font-weight: bold;
    color: #0b2545;
    border-bottom: 3pt solid #0b2545;
    padding-bottom: 4pt;
    margin-top: 0;
    margin-bottom: 12pt;
}}

/* Section headers */
h2 {{
    font-family: "Helvetica", "Arial", sans-serif;
    font-size: 14pt;
    font-weight: bold;
    color: #0b2545;
    margin-top: 18pt;
    margin-bottom: 6pt;
    border-bottom: 1pt solid #cccccc;
    padding-bottom: 2pt;
}}
h3 {{
    font-family: "Helvetica", "Arial", sans-serif;
    font-size: 11.5pt;
    font-weight: bold;
    color: #0b2545;
    margin-top: 12pt;
    margin-bottom: 4pt;
}}

p {{ margin: 0 0 7pt 0; }}

strong {{ color: #0b2545; }}

/* Horizontal rule */
hr {{
    border: none;
    border-top: 1pt solid #cccccc;
    margin: 12pt 0;
}}

/* Tables — xhtml2pdf supports basic table styling */
table {{
    border-collapse: collapse;
    width: 100%;
    margin: 6pt 0 10pt 0;
    font-size: 9.5pt;
}}
th, td {{
    border: 1pt solid #d0d0d0;
    padding: 4pt 6pt;
    text-align: left;
}}
th {{
    background-color: #0b2545;
    color: #ffffff;
    font-weight: bold;
}}

/* Inline code, code blocks */
code {{
    font-family: "Courier", monospace;
    font-size: 9pt;
    background-color: #f1f3f6;
    padding: 0 2pt;
}}
pre {{
    background-color: #f1f3f6;
    border-left: 3pt solid #0b2545;
    padding: 6pt 8pt;
    font-family: "Courier", monospace;
    font-size: 9pt;
}}

/* Lists */
ul, ol {{ margin: 3pt 0 7pt 18pt; }}
li {{ margin-bottom: 2pt; }}

/* Blockquote */
blockquote {{
    border-left: 3pt solid #0b2545;
    padding: 3pt 10pt;
    color: #444444;
    background-color: #f6f8fb;
    margin: 8pt 0;
}}

/* Images / figures */
img {{
    max-width: 100%;
    margin: 6pt 0 4pt 0;
}}

/* Header & footer running content (xhtml2pdf-specific) */
#header_content {{
    text-align: right;
    font-size: 8pt;
    color: #666666;
}}
#footer_content {{
    text-align: center;
    font-size: 8pt;
    color: #666666;
}}
</style>
</head>
<body>
<div id="header_content">Portfolio Risk Analysis &mdash; Pat Ploypairaoh</div>
<div id="footer_content">Page <pdf:pagenumber/> of <pdf:pagecount/></div>
{html_body}
</body>
</html>
"""

# Render
with open(OUTPUT_PDF, "wb") as f:
    result = pisa.CreatePDF(src=html_doc, dest=f, encoding="utf-8")

if result.err:
    print(f"xhtml2pdf reported {result.err} error(s)", file=sys.stderr)
    sys.exit(1)

size_kb = OUTPUT_PDF.stat().st_size / 1024
print(f"Wrote {OUTPUT_PDF} ({size_kb:.1f} KB)")