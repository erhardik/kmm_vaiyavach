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
        pdf.set_font("Gujarati", style, size)
    else:
        pdf.set_font("Helvetica", style, size)


def _format_en_date(value):
    if not value:
        return "-"
    return f"{value.day:02d}-{value.strftime('%B')}-{value.year}"


def generate_gujarati_pdf_fpdf2(header, line_rows, contact_info, filename="requirement-order.pdf"):
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos
    FONT = "Gujarati"

    CATEGORY_LABELS_GU = {
        "GENERAL": "જનરલ વસ્તુઓ",
        "STATIONERY": "સ્ટેશનરી",
        "MEDICAL": "મેડિકલ",
        "AYURVEDIC": "આયુર્વેદિક દવાઓ",
        "COLOR_MATERIAL": "રંગ સામગ્રી",
    }

    class GujaratiPDF(FPDF):
        def header(self):
            M = self.l_margin
            page_w = self.w - M - self.r_margin
            if self.page_no() == 1:
                logo_path = Path(settings.BASE_DIR) / "pdf_header.png"
                if logo_path.exists():
                    self.image(str(logo_path), x=M, y=self.t_margin, w=63, h=19.6)
                self.set_font(FONT, "", 11)
                self.set_xy(M + page_w - 55, self.t_margin)
                self.cell(55, 8, f"ફોર્મ નંબર - {header.order_number or '________'}", align="R")
                y = self.t_margin + 23
                self.set_font(FONT, "", 7.2)
                self.set_xy(M, y)
                self.cell(55, 5, "[ ] બધી વસ્તુઓ પેક થઈ")
                self.set_xy(M + 55, y)
                self.cell(55, 5, "[ ] વિતરણ માટે તૈયાર")
                self.set_xy(M + page_w - 50, y)
                self.cell(50, 5, "ચેક કરનાર: ____________________", align="R")
                self.line(M, y + 6, M + page_w, y + 6)
                self._header_bottom = y + 10
            else:
                self.set_font(FONT, "", 9)
                self.set_xy(M, self.t_margin)
                self.cell(page_w, 6, f"ફોર્મ નંબર - {header.order_number or '________'}")
                self.line(M, self.t_margin + 7, M + page_w, self.t_margin + 7)
                self._header_bottom = self.t_margin + 12

        def footer(self):
            self.set_y(-15)
            self.set_font(FONT, "", 7.2)
            self.cell(self.w / 2 - self.l_margin, 4, contact_info or "", new_x=XPos.RIGHT, new_y=YPos.LAST)
            self.cell(self.w / 2 - self.r_margin, 4, f"પાનું {self.page_no()}", align="R")

    pdf = GujaratiPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(left=15, top=15, right=15)
    pdf.set_auto_page_break(auto=True, margin=15)
    font_path = _resolve_font_path()
    pdf.add_font(FONT, "", font_path)
    pdf.add_font(FONT, "B", font_path)
    pdf.set_text_shaping(True)
    pdf.add_page()

    M = pdf.l_margin
    page_w = pdf.w - M - pdf.r_margin
    page_bottom = pdf.h - pdf.b_margin - 20
    ROW_H = 7
    SM = 8

    # === METADATA GRID ===
    grid_y = pdf._header_bottom
    hw = page_w / 2
    qw = page_w / 4

    def meta_cell(text, w, bold=False):
        pdf.set_font(FONT, "B" if bold else "", SM)
        pdf.cell(w, ROW_H, text, border=1)

    pdf.set_xy(M, grid_y)
    meta_cell(f"પૂજ્ય શ્રી : {header.pujya_shri_name or '-'}", hw)
    meta_cell(f"ઠાણા : {str(header.thana_count or '-')}", hw)
    grid_y += ROW_H

    pdf.set_xy(M, grid_y)
    meta_cell(f"વિસ્તાર : {header.area or '-'}", hw)
    meta_cell(f"ફોર્મ તારીખ : {_format_en_date(header.requirement_date)}", hw)
    grid_y += ROW_H

    pdf.set_xy(M, grid_y)
    meta_cell(f"હાલનું સરનામું : {header.current_address or '-'}", hw)
    meta_cell(f"ચાતુર્માસ સ્થળ સરનામું : {header.chaturmas_place_address or '-'}", hw)
    grid_y += ROW_H

    pdf.set_xy(M, grid_y)
    meta_cell(f"ચાતુર્માસ પ્રવેશ : {_format_en_date(header.chaturmas_entry_date)}", qw)
    meta_cell(f"જનાર : {header.volunteer_name or '-'}", qw)
    meta_cell(f"સંઘ/સ્થિર : {header.get_stay_type_display() or '-'}", hw)
    grid_y += ROW_H

    caretaker = f"{header.caretaker_name or '-'} {header.caretaker_mobile or ''}".strip()
    pdf.set_xy(M, grid_y)
    meta_cell(f"પૂજ્ય શ્રી સંભાળ લેનાર : {caretaker}", page_w)
    grid_y += ROW_H + 4

    # === TWO-COLUMN ITEM TABLE ===
    COL_W = (page_w - 6) / 2
    COL_GAP = 6
    col1_x = M
    col2_x = M + COL_W + COL_GAP
    TH = 5
    HH = 6
    CH = 5
    FS = 7

    def draw_col_headers(y):
        pdf.set_font(FONT, "B", FS)
        for cx in (col1_x, col2_x):
            pdf.set_xy(cx, y)
            pdf.cell(6, HH, "નં.", border=1, align="C")
            pdf.cell(COL_W - 6 - 18 - 10, HH, "વસ્તુનું નામ", border=1, align="C")
            pdf.cell(18, HH, "પ્રકાર/સાઈઝ", border=1, align="C")
            pdf.cell(10, HH, "નંગ", border=1, align="C")
        pdf.set_font(FONT, "", FS)
        return y + HH

    def draw_row(cx, cy, sr, name, size, qty):
        pdf.set_font(FONT, "", FS)
        pdf.set_xy(cx, cy)
        pdf.cell(6, TH, str(sr), border=1, align="C")
        pdf.cell(COL_W - 6 - 18 - 10, TH, name, border=1)
        pdf.cell(18, TH, size, border=1, align="C")
        pdf.cell(10, TH, str(qty), border=1, align="C")

    def draw_cat(cx, cy, label):
        pdf.set_font(FONT, "B", FS)
        pdf.set_xy(cx, cy)
        pdf.cell(COL_W, CH, label, border=1, align="C")
        pdf.set_font(FONT, "", FS)

    def draw_column(rows, cx, start_y):
        y = start_y
        prev_cat = None
        for idx, row in enumerate(rows):
            sr, name, size, qty, category = row[:5]
            if category != prev_cat:
                prev_cat = category
                cat_label = CATEGORY_LABELS_GU.get(category, category)
                if y + CH + TH > page_bottom:
                    return y, rows[idx:]
                draw_cat(cx, y, cat_label)
                y += CH
            if y + TH > page_bottom:
                return y, rows[idx:]
            draw_row(cx, y, sr, name, size, qty)
            y += TH
        return y, []

    # Extract remark lines
    remark_lines = (header.remarks or "").splitlines()
    has_remarks = any(line.strip() for line in remark_lines)
    REMARKS_H = 28

    # Split rows evenly for balanced two-column layout
    remaining_rows = line_rows
    page_no = 0

    while remaining_rows:
        page_no += 1
        if page_no > 1:
            pdf.add_page()
            col_start_y = draw_col_headers(pdf._header_bottom)
        else:
            col_start_y = draw_col_headers(grid_y)

        half = (len(remaining_rows) + 1) // 2
        left_batch = remaining_rows[:half]
        right_batch = remaining_rows[half:]

        col1_bottom, left_overflow = draw_column(left_batch, col1_x, col_start_y)
        col2_bottom, right_overflow = draw_column(right_batch, col2_x, col_start_y)

        overflow = (left_overflow or []) + (right_overflow or [])
        if overflow:
            remaining_rows = overflow
            continue

        remaining_rows = None

        # All items fit — position remarks
        ny = max(col1_bottom, col2_bottom) + 4

        if has_remarks and ny + REMARKS_H > page_bottom:
            pdf.add_page()
            ny = pdf._header_bottom + 4

        if has_remarks:
            pdf.rect(M, ny, page_w, REMARKS_H)
            pdf.set_font(FONT, "B", 9)
            pdf.set_xy(M + 3, ny + 2)
            pdf.cell(page_w - 6, 6, "નોંધ:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font(FONT, "", 7.2)
            y_in = pdf.get_y()
            for note in remark_lines[:4]:
                if note.strip():
                    pdf.set_xy(M + 4, y_in)
                    pdf.multi_cell(page_w - 8, 5, note.strip())
                    y_in = pdf.get_y()
                else:
                    y_in += 5
        else:
            pdf.set_font(FONT, "", 7.2)
            pdf.set_xy(M, ny)
            pdf.cell(page_w, 5, "--")

    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
