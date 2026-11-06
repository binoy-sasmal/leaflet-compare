import hashlib
import statistics
from pathlib import Path
from functools import lru_cache
import numpy as np
import pdfplumber
import pypdfium2 as pdfium
from .model import Document, Span

DPI = 180
MAX_PAGES = 12

def render_page(path, index, scale=DPI/72):
    with pdfium.PdfDocument(str(path)) as pdf:
        page=pdf[index]
        bitmap=page.render(scale=scale)
        image=bitmap.to_pil().copy()
        bitmap.close(); page.close()
        return image

@lru_cache(maxsize=1)
def engine():
    from rapidocr_onnxruntime import RapidOCR
    return RapidOCR(det_use_cuda=False, cls_use_cuda=False, rec_use_cuda=False,
                    intra_op_num_threads=2, inter_op_num_threads=2)

def group_lines(lines, page, prefix):
    """Group nearby lines using median line height, preserving visible text."""
    if not lines: return []
    lines=sorted(lines,key=lambda x:(x['bbox'][1],x['bbox'][0]))
    height=statistics.median(max(1,l['bbox'][3]-l['bbox'][1]) for l in lines)
    groups=[]
    for line in lines:
        if groups and line['bbox'][1]-groups[-1][-1]['bbox'][3] < height*.85:
            groups[-1].append(line)
        else: groups.append([line])
    spans=[]
    for i,group in enumerate(groups):
        boxes=[l['bbox'] for l in group]; scores=[l['score'] for l in group if l.get('score') is not None]
        spans.append(Span(f'{prefix}-p{page}-{i}', ' '.join(l['text'] for l in group),page,
                          [min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes)],
                          min(scores) if scores else None))
    return spans

def extract(path, ocr=False):
    path=Path(path)
    doc=Document(path.name,hashlib.sha256(path.read_bytes()).hexdigest(), 'rapidocr-onnxruntime' if ocr else 'pdfplumber')
    try:
        with pdfplumber.open(path) as pdf:
            if not 0<len(pdf.pages)<=MAX_PAGES: raise ValueError(f'Expected 1-{MAX_PAGES} pages')
            for index,page in enumerate(pdf.pages):
                width,height=float(page.width),float(page.height)
                doc.pages.append(dict(page=index+1,width=width,height=height))
                try:
                    lines=[]
                    if ocr:
                        image=render_page(path,index)
                        result,_=engine()(np.array(image))
                        sx,sy=width/image.width,height/image.height
                        for box,text,score in result or []:
                            xs=[p[0]*sx for p in box]; ys=[p[1]*sy for p in box]
                            lines.append(dict(text=text,bbox=[min(xs),min(ys),max(xs),max(ys)],score=float(score)))
                    else:
                        for line in page.extract_text_lines(layout=False):
                            lines.append(dict(text=line['text'],bbox=[line['x0'],line['top'],line['x1'],line['bottom']]))
                    spans=group_lines(lines,index+1,'rev' if ocr else 'ref')
                    doc.paragraphs.extend(spans)
                    if not spans: doc.issues.append(f'Page {index+1}: no readable text extracted')
                    if sum(len(s.text) for s in spans)<40: doc.issues.append(f'Page {index+1}: sparse extraction; inspect source')
                    if any(s.score is not None and s.score<.90 for s in spans):
                        doc.issues.append(f'Page {index+1}: OCR recognition score below heuristic 0.90')
                except Exception as exc:
                    doc.issues.append(f'Page {index+1}: extraction failed ({type(exc).__name__}: {exc})')
    except Exception as exc:
        doc.issues.append(f'Document extraction failed ({type(exc).__name__}: {exc})')
    return doc

