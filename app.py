import tempfile
from pathlib import Path
import streamlit as st
from leaflet_compare.comparison import compare
from leaflet_compare.reporting import readable, evidence_image
import json

st.set_page_config(page_title='Leaflet Compare',page_icon='ðŸ“„',layout='wide')
st.caption('INDEPENDENT SYNTHETIC EVALUATION')
st.title('Leaflet Compare')
st.write('Compare a reference text PDF with a scanned revision. Inspect the source before verifying a change.')
st.caption('No affiliation with Schlafender Hase, TVT compatibility, clinical suitability or regulatory compliance is claimed.')
with st.sidebar:
    st.header('Documents')
    ref=st.file_uploader('Reference text PDF',type='pdf')
    rev=st.file_uploader('Scanned revision PDF',type='pdf')
    demo=st.checkbox('Use synthetic quantity-change example',value=not(ref and rev))
    run=st.button('Compare documents',type='primary')
    st.caption('Local OCR. Files stay in this process and temporary disk storage. English prose; maximum 12 pages per file.')
if run:
    if demo:
        a=Path('data/dev-quantity/reference.pdf'); b=Path('data/dev-quantity/scan.pdf')
        if not a.exists(): st.error('Generate the dataset first: python -m tools.generate'); st.stop()
        contents=(a.read_bytes(),b.read_bytes())
    elif ref and rev: contents=(ref.getvalue(),rev.getvalue())
    else: st.warning('Choose two PDFs.'); st.stop()
    with st.spinner('Extracting, aligning and comparing locally...'),tempfile.TemporaryDirectory() as tmp:
        paths=(Path(tmp)/'reference.pdf',Path(tmp)/'revision.pdf')
        for p,data in zip(paths,contents): p.write_bytes(data)
        report=compare(*paths)
    st.session_state['report']=report; st.session_state['contents']=contents
if 'report' in st.session_state:
    report=st.session_state['report']
    c1,c2,c3=st.columns(3)
    c1.metric('Observed findings',len(report.findings)); c2.metric('Critical category',sum(f.critical for f in report.findings)); c3.metric('Extraction issues',len(report.issues))
    for issue in report.issues: st.warning(issue)
    st.info('Findings are unverified extraction differences. OCR scores are heuristic signals, not probabilities. A clean comparison cannot establish document correctness.')
    with tempfile.TemporaryDirectory() as tmp:
        paths=(Path(tmp)/'reference.pdf',Path(tmp)/'revision.pdf')
        for p,data in zip(paths,st.session_state['contents']): p.write_bytes(data)
        for f in report.findings:
            with st.expander(f'{f.id} Â· {f.category} Â· {f.status}',expanded=True):
                for col,span,path,label in zip(st.columns(2),(f.reference,f.revision),paths,('Reference','Scanned revision')):
                    with col:
                        st.subheader(label)
                        if span:
                            st.write(span.text); st.caption(f'Page {span.page} | box {span.bbox} | recognition score {span.score}')
                            try: st.image(evidence_image(path,span))
                            except Exception as exc: st.warning(f'Evidence rendering failed: {exc}')
                        else: st.write('No aligned paragraph')
                for reason in f.uncertainty: st.caption(reason)
                f.status=st.selectbox('Review status',['unreviewed','verified_change','ocr_artifact','unresolved'],index=['unreviewed','verified_change','ocr_artifact','unresolved'].index(f.status),key=f'status-{report.reference.sha256}-{report.revision.sha256}-{f.id}')
                f.reviewer_note=st.text_input('Reviewer note',value=f.reviewer_note,key=f'note-{report.reference.sha256}-{report.revision.sha256}-{f.id}')
        if not report.findings: st.write('No observed differences. Check extraction issues and source coverage.')
        st.download_button('Download JSON',json.dumps(report.to_dict(),indent=2),'report.json','application/json')
        st.download_button('Download review report',readable(report,paths),'review.html','text/html')
    with st.expander('Extraction provenance'):
        st.json({'reference':report.to_dict()['reference'],'revision':report.to_dict()['revision']})
