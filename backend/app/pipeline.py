import os, re, subprocess, tempfile
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image
import pytesseract
from .mrz import parse_mrz
from .forensics import analyze_image
from .validation import validate_mrz, assess_forensics

def render_pdf(path: str, outdir: str) -> list[str]:
    prefix=os.path.join(outdir,'page'); subprocess.run(['pdftoppm','-png','-r','160',path,prefix],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); return sorted(str(p) for p in Path(outdir).glob('page-*.png'))

def preprocess_for_ocr(path: str) -> str:
    img=Image.open(path).convert('RGB'); img.thumbnail((1800,1800)); out=path+'.ocr.png'; img.save(out, optimize=True); return out

def analyze_file(path: str,mime: str) -> dict:
    with tempfile.TemporaryDirectory(prefix='sih26188-') as td:
        pages=render_pdf(path,td) if mime=='application/pdf' else [path]; texts=[]; forensic=[]
        for page in pages[:6]:
            ocr_input=preprocess_for_ocr(page); texts.append(pytesseract.image_to_string(Image.open(ocr_input),config='--psm 6')); forensic.append(analyze_image(page))
        text='\n'.join(texts); mrz=parse_mrz(text); doc_type='passport' if mrz.get('format')=='TD3' or re.search(r'\bPASSPORT\b',text,re.I) else 'unknown'; extracted={'document_type':doc_type,'ocr_text':text[:12000],'mrz':mrz}; validation=validate_mrz(mrz); forensic_assessment=assess_forensics(forensic); extracted['validation']=validation
        return {'document_type':doc_type,'extracted_data':extracted,'forensics':forensic,'forensic_assessment':forensic_assessment,'pages_processed':min(len(pages),6),'processed_at':datetime.now(timezone.utc).isoformat()}
