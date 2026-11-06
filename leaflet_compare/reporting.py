import base64
import html
import io
import json
from pathlib import Path
from PIL import ImageDraw
from .extraction import render_page

def evidence_image(path, span):
    image=render_page(path,span.page-1,scale=1.25).convert('RGB')
    box=[v*1.25 for v in span.bbox]
    ImageDraw.Draw(image).rectangle(box,outline='#d34437',width=3)
    pad=24
    return image.crop((0,max(0,box[1]-pad),image.width,min(image.height,box[3]+pad)))

def readable(report, paths=None):
    esc=lambda value: html.escape(str(value))
    def excerpt(span, side):
        if span is None: return '<p><em>No aligned paragraph</em></p>'
        picture=''
        if paths:
            try:
                out=io.BytesIO(); evidence_image(paths[side],span).save(out,format='PNG')
                picture=f'<img alt="Highlighted source excerpt" src="data:image/png;base64,{base64.b64encode(out.getvalue()).decode()}">'
            except Exception as exc: picture=f'<p>Source rendering unavailable: {esc(exc)}</p>'
        return f'<p>{esc(span.text)}</p><small>Page {span.page}; box {esc(span.bbox)}; span {esc(span.id)}; score {esc(span.score)}</small>{picture}'
    items=''
    for f in report.findings:
        items+=f'<article><h2>{f.id}: {esc(f.category)} <span>{esc(f.status)}</span></h2><div class="pair"><section><h3>Reference</h3>{excerpt(f.reference,0)}</section><section><h3>Scanned revision</h3>{excerpt(f.revision,1)}</section></div><p>{esc("; ".join(f.uncertainty))}</p><p>Reviewer note: {esc(f.reviewer_note)}</p></article>'
    issues=''.join(f'<li>{esc(i)}</li>' for i in report.issues)
    return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Leaflet Compare review</title><style>body{{font:16px system-ui;background:#f3f6f8;color:#183341;max-width:1120px;margin:40px auto;padding:0 24px}}header,article{{background:white;padding:24px;margin:20px 0;border-radius:12px;border:1px solid #d7e2e6}}h1{{font-size:36px}}h2{{font-size:21px}}small{{overflow-wrap:anywhere}}span{{font-size:14px;color:#087e8b}}.pair{{display:grid;grid-template-columns:1fr 1fr;gap:24px}}img{{width:100%;margin-top:16px}}@media(max-width:700px){{.pair{{grid-template-columns:1fr}}}}</style><header><p>INDEPENDENT SYNTHETIC EVALUATION</p><h1>Leaflet Compare</h1><p>{len(report.findings)} observed findings | Review required: {report.requires_review}</p><p>Observed differences are not verified authoring changes. Recognition scores are not calibrated probabilities. No affiliation, TVT compatibility, clinical suitability or regulatory compliance is claimed.</p><ul>{issues}</ul></header>{items or '<article>No text differences detected. Inspect extraction coverage before drawing conclusions.</article>'}<footer><p>Reference: {esc(report.reference.name)}<br>SHA-256 {report.reference.sha256}</p><p>Revision: {esc(report.revision.name)}<br>SHA-256 {report.revision.sha256}</p><p>Rules {report.rules_version}; schema {report.schema_version}. PDF point boxes use the top-left origin.</p></footer></html>'''

def export(report, output, paths=None):
    output=Path(output); output.mkdir(parents=True,exist_ok=True)
    (output/'report.json').write_text(json.dumps(report.to_dict(),indent=2,ensure_ascii=False),encoding='utf-8')
    (output/'review.html').write_text(readable(report,paths),encoding='utf-8')
