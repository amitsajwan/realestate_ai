"""Small brochures built in the test: real PDFs with a text layer, written with pdfium's own page-object API."""
import ctypes
import io
from typing import List, Optional, Sequence

import pypdfium2 as pdfium
import pypdfium2.raw as raw

GULMOHAR = [
    # page 1: cover
    ["Gulmohar Heights", "Ranjangaon, Pune", "A project by Sai Developers",
     "MahaRERA Registration No.: P52100012345", "maharera.maharashtra.gov.in"],
    # page 2: amenities
    ["Amenities", "Swimming pool", "Gymnasium", "Jogging track", "Children's play area", "Clubhouse", "Landscaped garden"],
    # page 3: specifications
    ["Specifications", "Flooring: 2'x2' vitrified tiles in all rooms", "Kitchen: Granite platform with steel sink",
     "Doors: Laminated flush doors", "Electrical: Concealed copper wiring", "Windows: Aluminium sliding windows"],
    # page 4: floor plans
    ["Floor plans", "2 BHK | Carpet area 650 sq ft", "3 BHK | Carpet area 890 sq ft",
     "4 towers, G+14 floors, 240 units", "Spread over 5 acres of land"],
    # page 5: location and legal
    ["Location advantage", "Site address: Gat No. 12, Ranjangaon MIDC Road, Ranjangaon, Pune 412209",
     "Possession: December 2028", "Disclaimer: artist's impression. Not an offer."],
]


def text_pdf(pages: Sequence[Optional[Sequence[str]]], size=(595, 842)) -> bytes:
    """One page per entry, each line a text object; None makes a page with no text at all (as a scanned page reads)."""
    pdf = pdfium.PdfDocument.new()
    for lines in pages:
        page = pdf.new_page(*size)
        for i, line in enumerate(lines or []):
            obj = raw.FPDFPageObj_NewTextObj(pdf, b"Helvetica", 12.0)
            buf = ctypes.create_string_buffer((line + "\0").encode("utf-16-le"))
            raw.FPDFText_SetText(obj, ctypes.cast(buf, ctypes.POINTER(raw.FPDF_WCHAR)))
            raw.FPDFPageObj_Transform(obj, 1, 0, 0, 1, 40, size[1] - 60 - 20 * i)
            raw.FPDFPage_InsertObject(page, obj)
        raw.FPDFPage_GenerateContent(page)
        page.close()
    out = io.BytesIO()
    pdf.save(out)
    pdf.close()
    return out.getvalue()


def lines_of(pages: List[List[str]]) -> List[str]:
    return [ln for p in pages for ln in p]
