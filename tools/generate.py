"""Dataset authoring only. Application code never imports this module."""
import argparse
import hashlib
import io
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader, simpleSplit
from leaflet_compare.extraction import render_page

HEADER='SYNTHETIC EVALUATION MATERIAL - NOT FOR REAL USE'
FOOTER='Fictional decorative materials. No medical or real product instructions.'

def manifest(split):
    p=Path('evaluation')/f'{split}.json'
    if hashlib.sha256(p.read_bytes()).hexdigest()!=p.with_suffix('.sha256').read_text().strip():
        raise ValueError('Frozen manifest hash mismatch')
    return json.loads(p.read_text(encoding='utf-8'))

def digital(path,texts,template,layout=False):
    font='Times-Roman' if template=='narrow-serif' else 'Helvetica'
    width=330 if template=='narrow-serif' else 430
    if layout: width-=95
    c=canvas.Canvas(str(path),pagesize=(595,842),invariant=1)
    c.setTitle('SYNTHETIC EVALUATION MATERIAL')
    c.setFillColorRGB(.02,.36,.41);c.rect(0,760,595,82,fill=1,stroke=0)
    c.setFillColorRGB(1,1,1);c.setFont('Helvetica-Bold',11);c.drawString(42,795,HEADER)
    y=710
    for i,text in enumerate(texts):
        if not text: continue
        size=16 if i==0 else 13
        c.setFillColorRGB(.08,.16,.2);c.setFont(font,size)
        for line in simpleSplit(text,font,size,width):
            c.drawString(48,y,line);y-=19
        y-=28
    c.setFont('Helvetica',10);c.setFillColorRGB(.25,.35,.4);c.drawString(42,54,FOOTER)
    c.drawString(42,36,'Synthetic evaluation | Page 1')
    c.save()

def generate(root=Path('data'),split=None):
    for s in ([split] if split else ['dev','heldout']):
        for case in manifest(s):
            out=root/case['id'];out.mkdir(parents=True,exist_ok=True)
            digital(out/'reference.pdf',case['reference'],case['template'])
            digital(out/'revision.pdf',case['revision'],case['template'],case['layout'])
            im=render_page(out/'revision.pdf',0,scale=2.5).convert('RGB')
            if case['condition']=='blur_low_contrast': im=ImageEnhance.Contrast(im.filter(ImageFilter.GaussianBlur(1.2))).enhance(.45)
            if case['condition']=='rotation': im=im.rotate(2.5,resample=Image.Resampling.BICUBIC,fillcolor='white')
            if case['condition']=='obscured':
                # Deliberately conceal a region of the quantity paragraph.
                ImageDraw.Draw(im).rectangle((115,405,1000,460),fill='white')
            if case['condition']=='obscured': im=im.filter(ImageFilter.GaussianBlur(1.6))
            c=canvas.Canvas(str(out/'scan.pdf'),pagesize=(595,842),invariant=1)
            c.drawImage(ImageReader(im),0,0,595,842);c.save()
            # Ground-truth full reading text, only consumed by evaluation.
            expected=' '.join([HEADER,*[t for t in case['revision'] if t],FOOTER,'Synthetic evaluation | Page 1'])
            (out/'truth.txt').write_text(expected,encoding='utf-8')
            if case['id']=='dev-quantity': im.resize((744,1053)).save(out/'preview.png')
            print(case['id'],flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--split',choices=['dev','heldout']);a=p.parse_args();generate(split=a.split)
