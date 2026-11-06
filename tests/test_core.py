import json
from pathlib import Path
import pytest
from leaflet_compare.model import Document, Span
from leaflet_compare.text import normalize, categories
from leaflet_compare.extraction import group_lines, extract
from leaflet_compare.comparison import compare_documents
from leaflet_compare.reporting import export, readable
from tools.evaluate import match_findings, distance

def doc(texts,method='pdfplumber'):
    return Document('synthetic.pdf','a'*64,method,[dict(page=1,width=595,height=842)],
                    [Span(f's{i}',t,1,[10,10+i*30,300,30+i*30],.99 if method.startswith('rapidocr') else None) for i,t in enumerate(texts)])

@pytest.mark.parametrize('a,b,category',[
    ('Imaginary dust: 12 mg.','Imaginary dust: 21 mg.','quantity_unit'),
    ('Imaginary dust: 12 mg.','Imaginary dust: 12 g.','quantity_unit'),
    ('Do not open the prop.','Do open the prop.','negation'),
    ('Never fold the prop.','Fold the prop.','negation'),
    ('Warning: Blue prop.','','warning'),
    ('A long decorative paragraph.','','missing_paragraph')])
def test_critical_rules(a,b,category): assert category in categories(a,b)

def test_normalization_preserves_meaning():
    assert normalize('  Do NOT use 1.25 mg, +3%;  2-4! ')== 'do not use 1.25 mg, +3%; 2-4!'
    assert normalize('1.25 mg')!=normalize('125 mg')

def test_line_wrap_alignment():
    lines=[dict(text='Do not fold the',bbox=[10,10,100,20]),dict(text='imaginary display.',bbox=[10,25,100,35]),dict(text='Next paragraph.',bbox=[10,70,100,80])]
    spans=group_lines(lines,1,'rev')
    assert [s.text for s in spans]==['Do not fold the imaginary display.','Next paragraph.']
    rev=doc([]);rev.paragraphs=spans
    report=compare_documents(doc(['Do not fold the imaginary display.','Next paragraph.']),rev)
    assert not report.findings

def test_omission_does_not_shift_following_paragraphs():
    report=compare_documents(doc(['A decorative cube.','Warning: Do not fold.','The paper sleeve is silver.']),doc(['A decorative cube.','The paper sleeve is silver.']))
    assert len(report.findings)==1 and report.findings[0].category=='warning'

def test_empty_extraction_is_not_no_difference():
    report=compare_documents(doc(['Visible text.']),doc([]))
    assert report.requires_review and report.issues and not report.findings

def test_low_score_identical_text_routes_review():
    rev=doc(['No change.'],'rapidocr-onnxruntime');rev.issues=['Low recognition score']
    report=compare_documents(doc(['No change.']),rev)
    assert report.requires_review and not report.findings

def test_corrupt_pdf_is_explicit(tmp_path):
    p=tmp_path/'broken.pdf';p.write_bytes(b'not a pdf')
    result=extract(p)
    assert result.issues and not result.paragraphs and len(result.sha256)==64

def test_report_integrity_and_escape(tmp_path):
    report=compare_documents(doc(['The prop has 12 mg.']),doc(['The prop has 21 mg.'],'rapidocr-onnxruntime'))
    report.findings[0].reviewer_note='<script>alert(1)</script>'
    report.findings[0].status='verified_change'
    export(report,tmp_path)
    data=json.loads((tmp_path/'report.json').read_text())
    assert data['findings'][0]['reference']['id']==data['reference']['paragraphs'][0]['id']
    assert data['findings'][0]['reference']['bbox']==[10,10,300,30]
    assert data['findings'][0]['status']=='verified_change'
    assert '<script>' not in (tmp_path/'review.html').read_text()
    assert '&lt;script&gt;' in (tmp_path/'review.html').read_text()

def test_matching_is_one_to_one_and_category_sensitive():
    report=compare_documents(doc(['Prop: 12 mg.']),doc(['Prop: 21 mg.']))
    changes=[dict(category='quantity_unit',reference='Prop: 12 mg.',revision='Prop: 21 mg.')]
    matches,extra,missed=match_findings(report.findings*2,changes)
    assert len(matches)==1 and len(extra)==1 and not missed
    changes[0]['category']='wording'
    assert match_findings(report.findings,changes)[2]==[0]

def test_error_distance():
    assert distance('abc','adc')==1
    assert distance(['one','two'],['two'])==1


def test_spacing_ambiguity_does_not_manufacture_critical_change():
    assert categories('NOT FOR REAL USE', 'NOTFOR REALUSE') == ['wording']
    assert categories('Page 1', 'Page1') == ['wording']
    report=compare_documents(doc(['Do not fold.']),doc(['Donot fold.'],'rapidocr-onnxruntime'))
    assert report.requires_review and len(report.findings)==1
    assert report.findings[0].category=='wording'


def test_percentage_unit_loss_is_critical():
    assert categories('Imaginary glow: 12%.', 'Imaginary glow: 12.') == ['quantity_unit']
    assert categories('Imaginary glow: 12%.', 'Imaginary glow: 12 g.') == ['quantity_unit']
    assert categories('Imaginary glow: 12 mg.', 'Imaginary glow: 12 mcg.') == ['quantity_unit']
