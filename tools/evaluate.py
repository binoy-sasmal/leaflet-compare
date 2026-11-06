import argparse
from collections import defaultdict
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
from leaflet_compare.comparison import compare, CRITICAL
from leaflet_compare.text import normalize
from leaflet_compare.reporting import export
from tools.generate import manifest

def distance(a,b):
    previous=list(range(len(b)+1))
    for i,x in enumerate(a,1):
        row=[i]
        for j,y in enumerate(b,1): row.append(min(row[-1]+1,previous[j]+1,previous[j-1]+(x!=y)))
        previous=row
    return previous[-1]

def match_findings(findings, changes):
    used=set(); matches=[]; unmatched=[]
    for f in findings:
        for i,c in enumerate(changes):
            source=f.reference.text if f.reference else (f.revision.text if f.revision else '')
            expected=c['reference'] or c['revision']
            if i not in used and f.category==c['category'] and normalize(source)==normalize(expected):
                used.add(i);matches.append((f,i));break
        else: unmatched.append(f)
    return matches,unmatched,[i for i in range(len(changes)) if i not in used]

def summarize(rows):
    tp=sum(r['tp'] for r in rows);fp=sum(r['fp'] for r in rows);fn=sum(r['fn'] for r in rows)
    return dict(cases=len(rows),tp=tp,fp=fp,fn=fn,precision=tp/(tp+fp) if tp+fp else None,recall=tp/(tp+fn) if tp+fn else None,
                review_cases=sum(r['review'] for r in rows),critical_review_coverage=sum(r['critical_review_coverage'] for r in rows),critical_changes=tp+fn,
                false_alarm_findings_on_controls=sum(r['control_alarms'] for r in rows),control_cases=sum(r['control'] for r in rows),
                character_errors=sum(r['cer_errors'] for r in rows),characters=sum(r['characters'] for r in rows),
                word_errors=sum(r['wer_errors'] for r in rows),words=sum(r['words'] for r in rows))

def evaluate(split,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    rows=[]; categories=defaultdict(lambda:dict(tp=0,fp=0,fn=0));conditions=defaultdict(list)
    for case in manifest(split):
        p=Path('data')/case['id'];paths=(p/'reference.pdf',p/'scan.pdf')
        report=compare(*paths);export(report,output/case['id'],paths)
        matches,unmatched,missed=match_findings(report.findings,case['changes'])
        matched_ids={i for _,i in matches}
        for f,_ in matches: categories[f.category]['tp']+=1
        for f in unmatched: categories[f.category]['fp']+=1
        for i in missed: categories[case['changes'][i]['category']]['fn']+=1
        truth=normalize((p/'truth.txt').read_text(encoding='utf-8'))
        observed=normalize(' '.join(s.text for s in report.revision.paragraphs))
        coverage=0
        for c in case['changes']:
            if c['critical'] and (report.issues or any(f.reference and normalize(f.reference.text)==normalize(c['reference']) for f in report.findings)):
                coverage+=1
        row=dict(id=case['id'],condition=case['condition'],tp=sum(f.critical for f,_ in matches),fp=sum(f.critical for f in unmatched),
                 fn=sum(case['changes'][i]['critical'] for i in missed),review=report.requires_review,critical_review_coverage=coverage,
                 control=not case['changes'],control_alarms=len(report.findings) if not case['changes'] else 0,
                 findings=len(report.findings),issues=report.issues,
                 missed=[case['changes'][i] for i in missed],false_alarms=[dict(category=f.category,reference=f.reference.text if f.reference else '',revision=f.revision.text if f.revision else '') for f in unmatched],
                 cer_errors=distance(truth,observed),characters=len(truth),wer_errors=distance(truth.split(),observed.split()),words=len(truth.split()),
                 reference_pdf_sha256=report.reference.sha256,scan_pdf_sha256=report.revision.sha256)
        rows.append(row);conditions[case['condition']].append(row)
        print(f'{case["id"]}: TP={row["tp"]} FP={row["fp"]} FN={row["fn"]} findings={row["findings"]}',flush=True)
    result=dict(rules_version=report.rules_version,split=split,manifest_sha256=hashlib.sha256((Path('evaluation')/f'{split}.json').read_bytes()).hexdigest(),
                protocol_sha256=hashlib.sha256(Path('evaluation/PROTOCOL.md').read_bytes()).hexdigest(),
                source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path('leaflet_compare').glob('*.py'))},
                environment=dict(python=platform.python_version(),platform=platform.platform(),packages={p:importlib.metadata.version(p) for p in ['rapidocr-onnxruntime','onnxruntime','pypdfium2','pdfplumber','reportlab','pillow']}),
                summary=summarize(rows),by_category=dict(categories),by_condition={k:summarize(v) for k,v in conditions.items()},cases=rows)
    (output/'metrics.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    s=result['summary'];text=f'# {split} measured evaluation\n\n'
    text+=f'Critical detection: TP {s["tp"]}, FP {s["fp"]}, FN {s["fn"]}. Precision {s["precision"]}; recall {s["recall"]}.\n\n'
    text+=f'Review routing: {s["review_cases"]}/{s["cases"]} cases. Critical review coverage {s["critical_review_coverage"]}/{s["critical_changes"]}. Control false alarms: {s["false_alarm_findings_on_controls"]} findings across {s["control_cases"]} unchanged/layout cases.\n\n'
    text+=f'OCR CER: {s["character_errors"]}/{s["characters"]} = {s["character_errors"]/s["characters"]:.4f}. WER: {s["word_errors"]}/{s["words"]} = {s["word_errors"]/s["words"]:.4f}.\n\n'
    text+='|Category|TP|FP|FN|\n|---|---:|---:|---:|\n'
    for cat,v in result['by_category'].items():text+=f'|{cat}|{v["tp"]}|{v["fp"]}|{v["fn"]}|\n'
    text+='\n|Scan condition|Cases|TP|FP|FN|Review cases|\n|---|---:|---:|---:|---:|---:|\n'
    for cond,v in result['by_condition'].items():text+=f'|{cond}|{v["cases"]}|{v["tp"]}|{v["fp"]}|{v["fn"]}|{v["review_cases"]}|\n'
    text+='\n## Observed failures\n\n'
    for row in rows:
        if row['missed'] or row['false_alarms'] or row['issues']:
            text+=f'- **{row["id"]}**: missed={json.dumps(row["missed"])}; false alarms={json.dumps(row["false_alarms"])}; extraction issues={json.dumps(row["issues"])}.\n'
    text+='\nSynthetic English prose cases only. Review coverage is not detection accuracy. Scores are not probabilities; these results do not establish real-world safety. See metrics.json for source/input/environment hashes.\n'
    (output/'RESULTS.md').write_text(text,encoding='utf-8')
    print(json.dumps(s,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--split',required=True,choices=['dev','heldout']);p.add_argument('--output');a=p.parse_args()
    evaluate(a.split,a.output or f'runs/{a.split}')
