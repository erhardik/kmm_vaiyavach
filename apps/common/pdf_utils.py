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


def _has_gujarati(text):
    return any(0x0A80 <= ord(ch) <= 0x0AFF for ch in text)


def _auto_font(pdf, text, style="", size=8.4):
    if _has_gujarati(text):
        pdf.set_font("Guj", style, size)
    else:
        pdf.set_font("Helvetica", style, size)


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

    def label_cell(w, h, text, align="L", border=0, fill=False, size=7.2):
        _auto_font(pdf, text, "B", size)
        pdf.cell(w, h, text, align=align, border=border, fill=fill)

    def data_cell(w, h, text, align="L", border=0, fill=False, size=8):
        text = str(text) if text is not None else "-"
        _auto_font(pdf, text, "", size)
        pdf.cell(w, h, text, align=align, border=border, fill=fill)

    def mixed_cell(w, h, text, align="L", border=0, fill=False, size=8, is_label=False):
        text = str(text) if text is not None else ""
        _auto_font(pdf, text, "B" if is_label else "", size)
        pdf.cell(w, h, text, align=align, border=border, fill=fill)

    # Logo + Form number (form number label is Gujarati, order_number might be mixed)
    logo_path = Path(settings.BASE_DIR) / "pdf_header.png"
    if logo_path.exists():
        pdf.image(str(logo_path), x=M, y=M + 1, w=63, h=19.6)
    form_text = f"ફોર્મ નંબર - {header.order_number or '________'}"
    _auto_font(pdf, form_text, "", 11)
    pdf.set_xy(M + page_w - 55, M + 1)
    pdf.cell(55, 8, form_text, align="R")

    # Status checkboxes
    y_status = M + 23
    for i, label in enumerate(["[ ] બધી વસ્તુઓ પેક થઈ", "[ ] વિતરણ માટે તૈયાર"]):
        _auto_font(pdf, label, "", 7.2)
        pdf.set_xy(M + i * 55, y_status)
        pdf.cell(55, 5, label)
    _auto_font(pdf, "ચેક કરનાર", "", 7.2)
    pdf.set_xy(M + page_w - 50, y_status)
    pdf.cell(50, 5, "ચેક કરનાર: ____________________", align="R")
    pdf.line(M, y_status + 6, M + page_w, y_status + 6)

    # Basic info table
    y_basic = y_status + 8
    basic_data = [
        (True, "પૂજ્ય શ્રી", header.pujya_shri_name or "-"),
        (False, "ઠાણા", str(header.thana_count or "-")),
        (True, "વિસ્તાર", header.area or "-"),
        (False, "ફોર્મ તારીખ", _format_guj_date(header.requirement_date)),
        (True, "હાલનું સરનામું", header.current_address or "-"),
        (False, "ચાતુર્માસ સ્થળનું સરનામું", header.chaturmas_place_address or "-"),
        (True, "ચાતુર્માસ પ્રવેશ તારીખ", _format_guj_date(header.chaturmas_entry_date)),
        (False, "જનારનું નામ", header.volunteer_name or "-"),
        (True, "સંઘ ઉપાશ્રય / સ્થિરવાસ", header.get_stay_type_display() or "-"),
        (False, "સંભાળ લેનાર", f"{header.caretaker_name or '-'} {header.caretaker_mobile or ''}".strip()),
    ]
    col_widths = [32, 55, 32, page_w - 119]
    for i in range(0, len(basic_data), 2):
        row_idx = i // 2
        y = y_basic + row_idx * 5.5
        left_is_label, left_label, left_val = basic_data[i]
        right_is_label, right_label, right_val = basic_data[i + 1]
        pdf.set_xy(M, y)
        label_cell(col_widths[0], 5.5, left_label, size=7.2)
        data_cell(col_widths[1], 5.5, left_val, size=8)
        label_cell(col_widths[2], 5.5, right_label, size=7.2)
        data_cell(col_widths[3], 5.5, right_val, size=8)

    # Item section header
    y_items_header = y_basic + (len(basic_data) // 2) * 5.5 + 3
    pdf.set_draw_color(0)
    _auto_font(pdf, "વસ્તુ સૂચિ", "B", 8.4)
    pdf.set_xy(M, y_items_header)
    pdf.cell(page_w, 6, "વસ્તુ સૂચિ", align="C", border=1)

    # Item table header
    y_item_table = y_items_header + 6
    col_sr = 8
    col_name = page_w / 2 - col_sr - 30 - 12
    for side in range(2):
        x_base = M + side * page_w / 2
        pdf.set_xy(x_base, y_item_table)
        _auto_font(pdf, "નં.", "B", 7.2)
        pdf.cell(col_sr, 5.5, "નં.", align="C", border=1)
        _auto_font(pdf, "વસ્તુનું નામ", "B", 7.2)
        pdf.cell(col_name, 5.5, "વસ્તુનું નામ", align="C", border=1)
        _auto_font(pdf, "પ્રકાર/સાઈઝ", "B", 7.2)
        pdf.cell(30, 5.5, "પ્રકાર/સાઈઝ", align="C", border=1)
        _auto_font(pdf, "નંગ", "B", 7.2)
        pdf.cell(12, 5.5, "નંગ", align="C", border=1)

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
            data_cell(col_sr, 6, sr, align="C", size=7.2)
            data_cell(col_name, 6, name, size=8)
            data_cell(30, 6, size, align="C", size=7.2)
            data_cell(12, 6, qty, align="C", size=7.2)

    # Extra notes section
    y_extra = y_item_table + 5.5 + max_rows * 6 + 2
    _auto_font(pdf, "વધારાની વસ્તુઓ / નોંધ", "B", 8.4)
    pdf.set_xy(M, y_extra)
    pdf.cell(page_w, 6, "વધારાની વસ્તુઓ / નોંધ", align="C", border=1)
    notes = (header.remarks or "").splitlines() if header.remarks else []
    for i in range(4):
        y_note = y_extra + 6 + i * 6
        pdf.set_xy(M, y_note)
        note_text = notes[i] if i < len(notes) else ""
        data_cell(page_w, 6, note_text, size=8, border=1)

    # Note box
    y_note_title = y_extra + 6 + 4 * 6 + 2
    _auto_font(pdf, "નોંધ:", "B", 8)
    pdf.set_xy(M, y_note_title)
    pdf.cell(page_w, 5, "નોંધ:")
    pdf.rect(M, y_note_title + 6, page_w, 18)

    # Footer
    y_footer = 290
    pdf.line(M, y_footer, M + page_w, y_footer)
    _auto_font(pdf, contact_info or "", "", 7.2)
    pdf.set_xy(M, y_footer + 1)
    pdf.cell(page_w / 2, 4, contact_info or "")
    _auto_font(pdf, "Page 1 of 1", "", 7.2)
    pdf.cell(page_w / 2, 4, "Page 1 of 1", align="R")

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    pdf.output(response)
    return response
