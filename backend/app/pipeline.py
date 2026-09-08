import os, re, subprocess, tempfile
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image
import pytesseract
from .mrz import parse_mrz
from .forensics import analyze_image
from .validation import validate_mrz, assess_forensics

MAX_PDF_PAGES = 3
OCR_MAX_SIDE = 1400

def render_pdf(path: str, outdir: str) -> list[str]:
    prefix=os.path.join(outdir,'page')
    subprocess.run(['pdftoppm','-png','-r','120','-f','1','-l',str(MAX_PDF_PAGES),path,prefix],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    return sorted(str(p) for p in Path(outdir).glob('page-*.png'))

def ocr_image(path: str) -> str:
    with Image.open(path) as source:
        img=source.convert('RGB')
        img.thumbnail((OCR_MAX_SIDE,OCR_MAX_SIDE))
        return pytesseract.image_to_string(img,config='--psm 6',timeout=15)

def analyze_file(path: str,mime: str) -> dict:
    with tempfile.TemporaryDirectory(prefix='sih26188-') as td:
        pages=render_pdf(path,td) if mime=='application/pdf' else [path]
        pages=pages[:MAX_PDF_PAGES]
        texts=[]; forensic=[]
        for page in pages:
            texts.append(ocr_image(page))
            forensic.append(analyze_image(page))
        text='\n'.join(texts)
        mrz=parse_mrz(text)
        doc_type='passport' if mrz.get('format')=='TD3' or re.search(r'\bPASSPORT\b',text,re.I) else 'unknown'
        extracted={'document_type':doc_type,'ocr_text':text[:12000],'mrz':mrz}
        validation=validate_mrz(mrz)
        forensic_assessment=assess_forensics(forensic)
        extracted['validation']=validation
        return {'document_type':doc_type,'extracted_data':extracted,'forensics':forensic,'forensic_assessment':forensic_assessment,'pages_processed':len(pages),'processed_at':datetime.now(timezone.utc).isoformat()}
