"""PDF documents with Arabic and English text (FR-EXP, NFR-L10N-03; Increment 3 design, Section 7 and RQ-1).

fpdf2 with HarfBuzz shaping joins Arabic letters and orders right-to-left runs; Noto Sans carries Latin text and Noto
Naskh Arabic is the fallback for Arabic, so a line may mix both. In Arabic the page reads right to left: text is
right-aligned and table columns run from the right."""
from datetime import datetime
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import TableCellFillMode

from app.core import clock

FONTS = Path(__file__).resolve().parents[1] / "fonts"
INK, MUTED, LINE, HEAD = (17, 24, 39), (90, 98, 112), (210, 214, 220), (230, 240, 236)


class Document(FPDF):
    def __init__(self, lang: str, title: str, subtitle: str = "", landscape: bool = False):
        super().__init__(orientation="L" if landscape else "P", unit="mm", format="A4")
        self.lang = "ar" if lang == "ar" else "en"
        self.rtl = self.lang == "ar"
        self.doc_title, self.subtitle = title, subtitle
        self.generated = clock.now().astimezone(clock.RIYADH)
        for family, file in (("Sans", "NotoSans"), ("Naskh", "NotoNaskhArabic")):
            self.add_font(family, "", FONTS / f"{file}-Regular.ttf")
            self.add_font(family, "B", FONTS / f"{file}-Bold.ttf")
        self.set_text_shaping(True)
        self.set_fallback_fonts(["Naskh"])
        self.set_title(title)
        self.set_creator("InternSync")
        self.set_auto_page_break(True, margin=16)
        self.set_margins(14, 14, 14)
        self.add_page()

    @property
    def align(self) -> str:
        return "R" if self.rtl else "L"

    def header(self) -> None:
        self.set_font("Sans", "B", 15)
        self.set_text_color(*INK)
        self.cell(0, 9, self.doc_title, align=self.align, new_x="LMARGIN", new_y="NEXT")
        if self.subtitle:
            self.set_font("Sans", "", 10)
            self.set_text_color(*MUTED)
            self.cell(0, 6, self.subtitle, align=self.align, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*LINE)
        self.line(self.l_margin, self.get_y() + 1, self.w - self.r_margin, self.get_y() + 1)
        self.ln(4)
        self.set_text_color(*INK)

    def footer(self) -> None:
        """The page number at the reading start, the program and the time at the other side; kept in separate
        cells so Arabic words and Western digits never reorder each other."""
        self.set_y(-12)
        self.set_font("Sans", "", 8)
        self.set_text_color(*MUTED)
        # The page number alone: a total ("of n") is filled in after shaping and breaks the Arabic line.
        page = f"صفحة {self.page_no()}" if self.rtl else f"Page {self.page_no()}"
        self.cell(0, 5, page, align=self.align)
        self.set_x(self.l_margin)
        self.cell(0, 5, f"InternSync · {stamp_text(self.generated)}", align="L" if self.rtl else "R")

    def heading(self, text: str) -> None:
        self.ln(2)
        self.set_font("Sans", "B", 12)
        self.cell(0, 8, text, align=self.align, new_x="LMARGIN", new_y="NEXT")

    def paragraph(self, text: str, size: int = 10) -> None:
        self.set_font("Sans", "", size)
        self.multi_cell(0, 6, text, align=self.align, new_x="LMARGIN", new_y="NEXT")

    def facts(self, pairs: list[tuple[str, str]]) -> None:
        """Label and value lines."""
        self.set_font("Sans", "", 10)
        for label, value in pairs:
            self.multi_cell(0, 6, f"{label}: {value}", align=self.align, new_x="LMARGIN", new_y="NEXT")

    def grid(self, headers: list[str], rows: list[list[str]], widths: list[float], numeric: set[int] = frozenset(),
             size: int = 9) -> None:
        """A table; numeric columns are centred, text columns follow the page direction."""
        order = list(range(len(headers)))
        if self.rtl:
            order.reverse()
        aligns = tuple("CENTER" if i in numeric else ("RIGHT" if self.rtl else "LEFT") for i in order)
        self.set_font("Sans", "", size)
        self.set_draw_color(*LINE)
        with self.table(col_widths=tuple(widths[i] for i in order), text_align=aligns, line_height=6,
                        headings_style=None, cell_fill_color=HEAD, cell_fill_mode=TableCellFillMode.ROWS,
                        first_row_as_headings=False) as table:
            self.set_font("Sans", "B", size)
            head = table.row()
            for i in order:
                head.cell(headers[i])
            self.set_font("Sans", "", size)
            for values in rows:
                row = table.row()
                for i in order:
                    row.cell(values[i] if values[i] is not None else "—")
        self.ln(2)

    def render(self) -> bytes:
        return bytes(self.output())


def stamp_text(at: datetime) -> str:
    """DD/MM/YYYY HH:mm in Riyadh time (NFR-L10N-02)."""
    return at.astimezone(clock.RIYADH).strftime("%d/%m/%Y %H:%M")
