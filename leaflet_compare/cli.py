import argparse
from .comparison import compare
from .reporting import export

def main():
    parser=argparse.ArgumentParser(description='Local OCR comparison. No ground-truth inputs.')
    parser.add_argument('reference'); parser.add_argument('revision'); parser.add_argument('--output',default='runs/latest')
    args=parser.parse_args()
    report=compare(args.reference,args.revision)
    export(report,args.output,(args.reference,args.revision))
    print(f'{len(report.findings)} observed findings; {len(report.issues)} extraction issues; review required={report.requires_review}')
    return 2 if report.issues else 0

if __name__=='__main__': raise SystemExit(main())
