import os, re, subprocess, tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image
import pytesseract
from .mrz import parse_mrz
from .forensics import analyze_image
from .validation import validate_mrz, assess_forensics

# Local-first limits: the primary screening result must not wait on any external API.
MAX_PDF_PAGES = 3
PDF_FORENSIC_PAGES = 1
OCR_MAX_SIDE = 1200
OCR_TIMEOUT = 5
PDF_TEXT_TIMEOUT = 3


def render_pdf(path: str, outdir: str, pages: int = PDF_FORENSIC_PAGES) -> list[str]:
    prefix = os.path.join(outdir, 'page')
    subprocess.run(['pdftoppm', '-png', '-r', '100', '-f', '1', '-l', str(pages), path, prefix], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=8)
    return sorted(str(p) for p in Path(outdir).glob('page-*.png'))


def extract_pdf_text(path: str) -> str:
    try:
        result = subprocess.run(['pdftotext', '-layout', '-f', '1', '-l', str(MAX_PDF_PAGES), path, '-'], check=True, capture_output=True, text=True, timeout=PDF_TEXT_TIMEOUT)
        return result.stdout[:12000]
    except Exception:
        return ''


def ocr_image(path: str) -> str:
    with Image.open(path) as source:
        img = source.convert('RGB')
        img.thumbnail((OCR_MAX_SIDE, OCR_MAX_SIDE))
        return pytesseract.image_to_string(img, config='--psm 6', timeout=OCR_TIMEOUT)


def _analyze_page(page: str, do_ocr: bool = True) -> tuple[str, dict]:
    if not do_ocr:
        return '', analyze_image(page)
    with ThreadPoolExecutor(max_workers=2) as pool:
        ocr_future = pool.submit(ocr_image, page)
        forensic_future = pool.submit(analyze_image, page)
        return ocr_future.result(), forensic_future.result()


def analyze_file(path: str, mime: str) -> dict:
    """Run the primary local screening path only.

    External enrichment (Sightengine) is intentionally outside this function so
    OCR/MRZ/local-forensics can be persisted and shown without waiting on a network call.
    """
    with tempfile.TemporaryDirectory(prefix='sih26188-') as td:
        native_text = extract_pdf_text(path) if mime == 'application/pdf' else ''
        is_digital_pdf = len(native_text.strip()) >= 40
        pages = render_pdf(path, td, PDF_FORENSIC_PAGES) if mime == 'application/pdf' else [path]
        pages = pages[:MAX_PDF_PAGES]
        if not pages:
            return {'document_type': 'unknown', 'extracted_data': {'document_type': 'unknown', 'ocr_text': '', 'mrz': {}}, 'forensics': [], 'forensic_assessment': {'status': 'not_evaluated'}, 'pages_processed': 0, 'processed_at': datetime.now(timezone.utc).isoformat()}

        # Digital PDFs use the native text layer and skip Tesseract.
        # Scanned PDFs/images use OCR and local forensics in parallel.
        with ThreadPoolExecutor(max_workers=3) as pool:
            page_futures = [pool.submit(_analyze_page, page, do_ocr=not is_digital_pdf) for page in pages]
            results = [future.result() for future in page_futures]

        ocr_text = '\n'.join(result[0] for result in results)
        text = native_text if is_digital_pdf else ocr_text
        forensic = [result[1] for result in results]
        mrz = parse_mrz(text)
        doc_type = 'passport' if mrz.get('format') == 'TD3' or re.search(r'\bPASSPORT\b', text, re.I) else 'unknown'
        extracted = {'document_type': doc_type, 'ocr_text': text[:12000], 'mrz': mrz}
        validation = validate_mrz(mrz)
        forensic_assessment = assess_forensics(forensic)
        extracted['validation'] = validation
        return {'document_type': doc_type, 'extracted_data': extracted, 'forensics': forensic, 'forensic_assessment': forensic_assessment, 'pages_processed': len(pages), 'processed_at': datetime.now(timezone.utc).isoformat()}
