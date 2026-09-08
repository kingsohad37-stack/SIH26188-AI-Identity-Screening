import os, re, subprocess, tempfile
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image
import pytesseract
from .mrz import parse_mrz
from .forensics import analyze_image
from .validation import validate_mrz, assess_forensics
from .sightengine import analyze_image as analyze_with_sightengine

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
        return pytesseract.image_to_string(img,config='--psm 6',timeout=8)

def analyze_file(path: str,mime: str) -> dict:
    with tempfile.TemporaryDirectory(prefix='sih26188-') as td:
        pages=render_pdf(path,td) if mime=='application/pdf' else [path]
        pages=pages[:MAX_PDF_PAGES]
        texts=[]; forensic=[]
        for page in pages:
            texts.append(ocr_image(page))
            forensic.append(analyze_image(page))
        # One external call on the first page keeps the external forensic signal useful without multiplying latency.
        sightengine=analyze_with_sightengine(pages[0]) if pages else {'available':False,'status':'not_evaluated'}
        text='\n'.join(texts)
        mrz=parse_mrz(text)
        doc_type='passport' if mrz.get('format')=='TD3' or re.search(r'\bPASSPORT\b',text,re.I) else 'unknown'
        extracted={'document_type':doc_type,'ocr_text':text[:12000],'mrz':mrz}
        validation=validate_mrz(mrz)
        forensic_assessment=assess_forensics(forensic)
        recapture=((sightengine.get('response') or {}).get('recapture') or {}).get('score')
        genai=((sightengine.get('response') or {}).get('genai') or {}).get('score')
        if isinstance(recapture,(int,float)) and recapture > 0.5:
            forensic_assessment={'status':'suspicious','reason':'Sightengine detected a likely recapture from a screen or printout.','sightengine_recapture_score':recapture,**forensic_assessment}
        elif isinstance(genai,(int,float)) and genai > 0.8:
            forensic_assessment={'status':'suspicious','reason':'Sightengine detected a high likelihood of AI-generated image content.','sightengine_genai_score':genai,**forensic_assessment}
        extracted['validation']=validation
        return {'document_type':doc_type,'extracted_data':extracted,'forensics':forensic,'forensic_assessment':forensic_assessment,'sightengine':sightengine,'pages_processed':len(pages),'processed_at':datetime.now(timezone.utc).isoformat()}
