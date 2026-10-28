"""The certificate page (FR-CER-01; Increment 4 design, Section 4 and RQ-4): A4 landscape, English on the left,
Arabic on the right, the QR code of the public page at the bottom. No grade is printed."""
from dataclasses import dataclass
from datetime import date, datetime

import qrcode
from fpdf import FPDF

from app.core import clock
from app.exports.pdf import FONTS, INK, LINE, MUTED

GREEN = (31, 56, 100)
TYPE = {"coop": ("co-op training", "التدريب التعاوني"), "summer": ("summer training", "التدريب الصيفي")}


@dataclass(frozen=True)
class Facts:
    code: str
    url: str
    name_en: str
    name_ar: str
    university_en: str
    university_ar: str
    college_en: str
    college_ar: str
    cycle: str
    training_type: str
    company: str
    start: date
    end: date
    issued_at: datetime


def grouped(code: str) -> str:
    """The code in groups of four, easier to read and type from paper; the lookup ignores the dashes."""
    return "-".join(code[i:i + 4] for i in range(0, len(code), 4))


def _day(d: date | datetime) -> str:
    if isinstance(d, datetime):
        d = d.astimezone(clock.RIYADH).date()
    return d.strftime("%d/%m/%Y")


def qr_image(url: str):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").get_image()


class _Page(FPDF):
    def __init__(self):
        super().__init__(orientation="L", unit="mm", format="A4")
        for family, file in (("Sans", "NotoSans"), ("Naskh", "NotoNaskhArabic")):
            self.add_font(family, "", FONTS / f"{file}-Regular.ttf")
            self.add_font(family, "B", FONTS / f"{file}-Bold.ttf")
        self.set_text_shaping(True)
        self.set_fallback_fonts(["Naskh"])
        self.set_auto_page_break(False)
        self.set_creator("InternSync")
        self.add_page()

    def text_at(self, x: float, y: float, w: float, h: float, text: str, size: float, style: str = "",
                align: str = "L", color=INK) -> None:
        self.set_xy(x, y)
        self.set_font("Sans", style, size)
        self.set_text_color(*color)
        self.multi_cell(w, h, text, align=align)


def render(f: Facts) -> bytes:
    pdf = _Page()
    pdf.set_title(f"Certificate {f.code}")
    pdf.set_draw_color(*GREEN)
    pdf.set_line_width(1.2)
    pdf.rect(10, 10, 277, 190)
    pdf.set_draw_color(*LINE)
    pdf.set_line_width(0.3)
    pdf.rect(14, 14, 269, 182)

    pdf.text_at(14, 22, 269, 8, "InternSync", 11, "B", "C", MUTED)
    pdf.text_at(20, 32, 128, 12, "Certificate of Completion", 22, "B", "L", GREEN)
    pdf.text_at(149, 32, 128, 12, "شهادة إتمام التدريب", 22, "B", "R", GREEN)
    pdf.set_draw_color(*LINE)
    pdf.line(148.5, 50, 148.5, 140)

    kind_en, kind_ar = TYPE.get(f.training_type, TYPE["coop"])
    start, end = _day(f.start), _day(f.end)
    pdf.text_at(20, 54, 122, 7, "This certifies that", 12, "", "L", MUTED)
    pdf.text_at(20, 63, 122, 10, f.name_en, 18, "B", "L")
    pdf.text_at(20, 78, 122, 7, f"has completed the {kind_en} of the cycle \"{f.cycle}\" at {f.company}, "
                                f"from {start} to {end}.", 12)
    pdf.text_at(20, 112, 122, 7, f"{f.college_en}\n{f.university_en}", 11, "", "L", MUTED)

    pdf.text_at(155, 54, 122, 7, "تشهد هذه الوثيقة بإتمام", 12, "", "R", MUTED)
    pdf.text_at(155, 63, 122, 10, f.name_ar, 18, "B", "R")
    # Arabic sentences and Western digits are kept in separate lines so the dates never change places.
    pdf.text_at(155, 78, 122, 7, f"{kind_ar} ضمن دورة «{f.cycle}» لدى {f.company}.", 12, "", "R")
    pdf.text_at(155, 94, 122, 7, f"من {start}", 12, "", "R")
    pdf.text_at(155, 101, 122, 7, f"إلى {end}", 12, "", "R")
    pdf.text_at(155, 112, 122, 7, f"{f.college_ar}\n{f.university_ar}", 11, "", "R", MUTED)

    pdf.image(qr_image(f.url), x=128.5, y=142, w=40, h=40)
    pdf.text_at(20, 150, 100, 6, f"Issued {_day(f.issued_at)}", 10, "", "L", MUTED)
    pdf.text_at(20, 157, 100, 6, f"Certificate code: {grouped(f.code)}", 10, "B", "L")
    pdf.text_at(20, 164, 100, 6, "Scan the code or open the address below to verify. The grade is not shown.",
                9, "", "L", MUTED)
    pdf.text_at(177, 150, 100, 6, f"تاريخ الإصدار {_day(f.issued_at)}", 10, "", "R", MUTED)
    pdf.text_at(177, 157, 100, 6, "رمز الشهادة", 10, "B", "R")
    pdf.text_at(177, 164, 100, 6, grouped(f.code), 10, "B", "R")
    pdf.text_at(177, 171, 100, 6, "امسح الرمز للتحقق. لا تظهر الدرجة.", 9, "", "R", MUTED)
    pdf.text_at(14, 186, 269, 6, f.url, 9, "", "C", MUTED)
    return bytes(pdf.output())
