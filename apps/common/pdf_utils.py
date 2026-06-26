from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
except Exception:
    HTML = None
    CSS = None
    FontConfiguration = None

FONT_PATH = Path(settings.GUJARATI_FONT_PATH)
GUJARATI_FONT_NAME = "NotoSansGujarati"

_gujarati_font_registered = False
if FONT_PATH.exists():
    try:
        pdfmetrics.registerFont(TTFont(GUJARATI_FONT_NAME, str(FONT_PATH)))
        _gujarati_font_registered = True
    except Exception:
        pass


def get_gujarati_style(font_size=12):
    styles = getSampleStyleSheet()
    return ParagraphStyle(
        name=f"Gujarati_{font_size}",
        parent=styles["Normal"],
        fontName=GUJARATI_FONT_NAME,
        fontSize=font_size,
        leading=int(font_size * 1.35),
    )


def shape_text(data, font_size=12):
    if data is None:
        return ""
    if isinstance(data, list):
        return [shape_text(item, font_size) for item in data]
    if isinstance(data, str):
        return Paragraph(data, get_gujarati_style(font_size))
    return data


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        page_count = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_footer(page_count)
            super().showPage()
        super().save()

    def draw_footer(self, page_count):
        pass


def generate_weasyprint_pdf(template_name, context, filename="document.pdf", extra_css=None, font_path=None):
    font_config = FontConfiguration() if FontConfiguration else None
    resolved_font_path = str(font_path or settings.GUJARATI_FONT_PATH)
    context.setdefault("font_path", resolved_font_path)
    html_string = render_to_string(template_name, context)
    html = HTML(string=html_string)

    font_src = resolved_font_path.replace("\\", "/")
    base_css = CSS(string=f"""
        @page {{ size: A4; margin: 8mm 8mm 10mm 8mm; }}
        @font-face {{
            font-family: 'Noto Sans Gujarati';
            src: url('file:///{font_src.lstrip("/")}') format('truetype');
        }}
        *, html, body, div, span, p, a, h1, h2, h3, h4, h5, h6, table, tr, th, td, b, strong, i, em {{
            font-family: 'Noto Sans Gujarati', Arial, sans-serif !important;
            text-rendering: optimizeLegibility !important;
            font-variant-ligatures: common-ligatures !important;
            font-feature-settings: "liga" 1, "clig" 1, "calt" 1, "akhn" 1, "rphf" 1, "blwf" 1, "pstf" 1, "vattu" 1, "cjct" 1 !important;
        }}
        p, td, th, span, div {{
            word-break: keep-all !important;
            white-space: normal !important;
        }}
    """)

    stylesheets = [base_css]
    if extra_css:
        stylesheets.append(CSS(string=extra_css))

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    kwargs = {"font_config": font_config} if font_config else {}
    html.write_pdf(target=response, stylesheets=stylesheets, **kwargs)
    return response
