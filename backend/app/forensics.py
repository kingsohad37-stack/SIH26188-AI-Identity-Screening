import cv2
import numpy as np
from PIL import Image

def _ela(path: str, quality: int = 90) -> dict:
    try:
        original=Image.open(path).convert("RGB")
        if original.width<64 or original.height<64: return {"available":False,"reason":"image_too_small"}
        import io
        buf=io.BytesIO(); original.save(buf,format="JPEG",quality=quality); buf.seek(0); recompressed=Image.open(buf).convert("RGB")
        a=np.asarray(original,dtype=np.int16); b=np.asarray(recompressed,dtype=np.int16); diff=np.abs(a-b).mean(axis=2); p95=float(np.percentile(diff,95)); mean=float(diff.mean()); high=float((diff>max(12.0,p95)).mean())
        return {"available":True,"mean_error":round(mean,4),"p95_error":round(p95,4),"high_error_area_ratio":round(high,6),"interpretation":"Localized recompression differences are a review signal; they do not prove editing."}
    except Exception as exc: return {"available":False,"reason":type(exc).__name__}

def _jpeg_metadata(path: str) -> dict:
    try:
        img=Image.open(path); return {"format":img.format,"mode":img.mode,"exif_present":bool(img.getexif()),"exif_keys":sorted(str(k) for k in img.getexif().keys())[:40]}
    except Exception: return {"format":None,"mode":None,"exif_present":False,"exif_keys":[]}

def analyze_image(path: str) -> dict:
    img=cv2.imread(path)
    if img is None: return {"available":False,"reason":"image_decode_failed"}
    gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY); lap_var=float(cv2.Laplacian(gray,cv2.CV_64F).var()); edges=cv2.Canny(gray,80,160); edge_density=float(np.count_nonzero(edges)/edges.size); h,w=gray.shape; ela=_ela(path); meta=_jpeg_metadata(path); quality_flags=[]
    if lap_var<20: quality_flags.append("very_low_sharpness")
    if lap_var>5000: quality_flags.append("very_high_local_contrast")
    return {"available":True,"width":int(w),"height":int(h),"laplacian_variance":round(lap_var,3),"edge_density":round(edge_density,6),"ela":ela,"metadata":meta,"quality_flags":quality_flags,"signals":["sharpness_signal_available","edge_density_signal_available","ela_recompression_signal_available","image_metadata_signal_available"],"limitation":"Forensic signals are screening evidence only. They do not establish authenticity without a validated classifier and corroborating evidence."}
