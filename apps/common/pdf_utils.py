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


def _resolve_font_path():
    path = Path(settings.GUJARATI_FONT_PATH)
    if path.exists():
        return str(path)
    for candidate in [
        Path(settings.BASE_DIR) / "static" / "fonts" / "NotoSansGujarati-Regular.ttf",
        Path(settings.BASE_DIR) / "assets/fonts/NotoSansGujarati-Regular.ttf",
    ]:
        if candidate.exists():
            return str(candidate)
    return str(path)


def _format_guj_date(value):
    if not value:
        return "-"
    month_names_gu = [
        "જાન્યુઆરી", "ફેબ્રુઆરી", "માર્ચ", "એપ્રિલ",
        "મે", "જૂન", "જુલાઈ", "ઑગસ્ટ",
        "સપ્ટેમ્બર", "ઓક્ટોબર", "નવેમ્બર", "ડિસેમ્બર",
    ]
    return f"{value.day:02d}-{month_names_gu[value.month - 1]}-{value.year}"


def generate_gujarati_pdf_fpdf2(header, line_rows, contact_info, filename="requirement-order.pdf"):
    from fpdf import FPDF

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()

    font_path = _resolve_font_path()
    pdf.add_font("Guj", "", font_path)
    pdf.add_font("Guj", "B", font_path)
    pdf.add_font("Guj", "I", font_path)
    pdf.add_font("Guj", "BI", font_path)

    M = 8
    pdf.set_margins(M, M, M)
    page_w = 210 - 2 * M

    def set_font(style="", size=8.4):
        pdf.set_font("Guj", style, size)

    def cell(w, h, text, align="L", border=0, fill=False):
        pdf.cell(w, h, text, align=align, border=border, fill=fill)

    # Logo + Form number
    logo_path = Path(settings.BASE_DIR) / "pdf_header.png"
    if logo_path.exists():
        pdf.image(str(logo_path), x=M, y=M + 1, w=63, h=19.6)
    set_font(size=11)
    pdf.set_xy(M + page_w - 50, M + 1)
    pdf.cell(50, 8, f"ફોર્મ નંબર - {header.order_number or '________'}", align="R")

    # Status checkboxes
    y_status = M + 23
    set_font(size=7.2)
    pdf.set_xy(M, y_status)
    cell(50, 5, "[ ] બધી વસ્તુઓ પેક થઈ")
    cell(50, 5, "[ ] વિતરણ માટે તૈયાર")
    pdf.set_xy(M + page_w - 45, y_status)
    cell(45, 5, "ચેક કરનાર: ____________________", align="R")
    pdf.line(M, y_status + 6, M + page_w, y_status + 6)

    # Basic info table
    y_basic = y_status + 8
    basic_data = [
        ("પૂજ્ય શ્રી", header.pujya_shri_name or "-", "ઠાણા", str(header.thana_count or "-")),
        ("વિસ્તાર", header.area or "-", "ફોર્મ તારીખ", _format_guj_date(header.requirement_date)),
        ("હાલનું સરનામું", header.current_address or "-", "ચાતુર્માસ સ્થળનું સરનામું", header.chaturmas_place_address or "-"),
        ("ચાતુર્માસ પ્રવેશ તારીખ", _format_guj_date(header.chaturmas_entry_date), "જનારનું નામ", header.volunteer_name or "-"),
        ("સંઘ ઉપાશ્રય / સ્થિરવાસ", header.get_stay_type_display() or "-", "સંભાળ લેનાર", f"{header.caretaker_name or '-'} {header.caretaker_mobile or ''}".strip()),
    ]
    col_widths = [29, 55, 33, page_w - 117]
    for row_idx, (lbl1, val1, lbl2, val2) in enumerate(basic_data):
        y = y_basic + row_idx * 5.5
        pdf.set_xy(M, y)
        set_font(style="B", size=7.2)
        cell(col_widths[0], 5.5, lbl1, border=1)
        set_font(size=8)
        cell(col_widths[1], 5.5, val1, border=1)
        set_font(style="B", size=7.2)
        cell(col_widths[2], 5.5, lbl2, border=1)
        set_font(size=8)
        cell(col_widths[3], 5.5, val2, border=1)

    # Item section header
    y_items_header = y_basic + len(basic_data) * 5.5 + 3
    pdf.set_draw_color(0)
    pdf.set_xy(M, y_items_header)
    set_font(style="B", size=8.4)
    cell(page_w, 6, "વસ્તુ સૂચિ", align="C", border=1)

    # Item table header
    y_item_table = y_items_header + 6
    col_sr = 8
    col_name = page_w / 2 - col_sr - 30 - 12
    set_font(style="B", size=7.2)
    for side in range(2):
        x_base = M + side * page_w / 2
        pdf.set_xy(x_base, y_item_table)
        cell(col_sr, 5.5, "નં.", align="C", border=1)
        cell(col_name, 5.5, "વસ્તુનું નામ", align="C", border=1)
        cell(30, 5.5, "પ્રકાર/સાઈઝ", align="C", border=1)
        cell(12, 5.5, "નંગ", align="C", border=1)

    # Item rows (two columns)
    half = (len(line_rows) + 1) // 2
    left_col = line_rows[:half]
    right_col = line_rows[half:]
    max_rows = max(len(left_col), len(right_col))

    for idx in range(max_rows):
        y_row = y_item_table + 5.5 + idx * 6
        for side in range(2):
            col = left_col if side == 0 else right_col
            if idx >= len(col):
                continue
            sr, name, size, qty = col[idx]
            x_base = M + side * page_w / 2
            pdf.set_xy(x_base, y_row)
            set_font(size=7.2)
            cell(col_sr, 6, str(sr), align="C", border=1)
            set_font(size=8)
            cell(col_name, 6, str(name), border=1)
            set_font(size=7.2)
            cell(30, 6, str(size), align="C", border=1)
            cell(12, 6, str(qty), align="C", border=1)

    # Extra notes section
    y_extra = y_item_table + 5.5 + max_rows * 6 + 2
    set_font(style="B", size=8.4)
    pdf.set_xy(M, y_extra)
    cell(page_w, 6, "વધારાની વસ્તુઓ / નોંધ", align="C", border=1)
    notes = (header.remarks or "").splitlines() if header.remarks else []
    for i in range(4):
        y_note = y_extra + 6 + i * 6
        pdf.set_xy(M, y_note)
        note_text = notes[i] if i < len(notes) else ""
        cell(page_w, 6, note_text, border=1)

    # Note box
    y_note_title = y_extra + 6 + 4 * 6 + 2
    set_font(style="B", size=8)
    pdf.set_xy(M, y_note_title)
    cell(page_w, 5, "નોંધ:")
    pdf.rect(M, y_note_title + 6, page_w, 18)

    # Footer
    y_footer = 290
    pdf.line(M, y_footer, M + page_w, y_footer)
    set_font(size=7.2)
    pdf.set_xy(M, y_footer + 1)
    pdf.cell(page_w / 2, 4, contact_info or "")
    pdf.cell(page_w / 2, 4, "Page 1 of 1", align="R")

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    pdf.output(response)
    return response
