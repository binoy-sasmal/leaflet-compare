from .model import Finding, Report
from .alignment import align
from .text import normalize, categories
from .extraction import extract

CRITICAL = {'quantity_unit','negation','warning','missing_paragraph'}

def compare_documents(reference, revision):
    issues=[f'Reference: {s}' for s in reference.issues]+[f'Revision: {s}' for s in revision.issues]
    if len(reference.pages)!=len(revision.pages): issues.append('Page counts differ; review completeness')
    findings=[]
    # Unreadable documents do not turn every paragraph into a claimed deletion.
    if not reference.paragraphs or not revision.paragraphs:
        issues.append('Comparison incomplete: a document has no readable paragraphs')
        return Report(reference,revision,findings,issues)
    for a,b,score in align(reference.paragraphs,revision.paragraphs):
        at,bt=a.text if a else '',b.text if b else ''
        if normalize(at)==normalize(bt): continue
        uncertainty=['OCR text may differ from source; verify page evidence'] if revision.method.startswith('rapidocr') else []
        if a is None or b is None: uncertainty.append('Unmatched paragraph; inspect alignment and extraction completeness')
        elif score<.75: uncertainty.append('Weak paragraph alignment')
        if b and b.score is not None and b.score<.90: uncertainty.append('Low OCR recognition score (uncalibrated)')
        for category in categories(at,bt):
            findings.append(Finding(f'F{len(findings)+1:03}',category,category in CRITICAL,a,b,uncertainty.copy()))
    return Report(reference,revision,findings,issues)

def compare(reference_path, revision_path):
    return compare_documents(extract(reference_path),extract(revision_path,ocr=True))
