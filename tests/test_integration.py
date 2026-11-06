import pytest
import pdfplumber
from leaflet_compare.comparison import compare
from tools.generate import digital, generate
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from leaflet_compare.extraction import render_page

@pytest.mark.ocr
def test_end_to_end_scanned_quantity(tmp_path):
    ref=tmp_path/'reference.pdf';rev=tmp_path/'revision.pdf';scan=tmp_path/'scan.pdf'
    digital(ref,['FICTIONAL PROP','Each prop contains 12 mg of imaginary dust.'],'wide-sans')
    digital(rev,['FICTIONAL PROP','Each prop contains 21 mg of imaginary dust.'],'wide-sans')
    image=render_page(rev,0)
    c=canvas.Canvas(str(scan),pagesize=(595,842),invariant=1);c.drawImage(ImageReader(image),0,0,595,842);c.save()
    with pdfplumber.open(scan) as p: assert not p.pages[0].extract_text()
    report=compare(ref,scan)
    quantities=[f for f in report.findings if f.category=='quantity_unit']
    assert any('12 mg' in f.reference.text and '21 mg' in f.revision.text for f in quantities)
    assert all(f.reference.page==1 and len(f.revision.bbox)==4 for f in quantities)
    assert report.requires_review
