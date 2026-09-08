import os
import cv2
import numpy as np
from pathlib import Path

MODELS_DIR=Path(os.getenv('MODELS_DIR','/app/models')); DETECTOR=MODELS_DIR/'face_detection_yunet_2023mar.onnx'; RECOGNIZER=MODELS_DIR/'face_recognition_sface_2021dec.onnx'
class FaceEngine:
    def __init__(self):
        if not DETECTOR.exists() or not RECOGNIZER.exists(): raise RuntimeError('Face model files are not installed')
        self.detector=cv2.FaceDetectorYN.create(str(DETECTOR),'',(320,320),0.8,0.3,5000); self.recognizer=cv2.FaceRecognizerSF.create(str(RECOGNIZER),'')
    def embedding(self,image:np.ndarray):
        if image is None or image.size==0: return None,{'status':'not_evaluated','reason':'Invalid image'}
        h,w=image.shape[:2]; self.detector.setInputSize((w,h)); _,faces=self.detector.detect(image)
        if faces is None or len(faces)==0: return None,{'status':'not_evaluated','reason':'No face detected'}
        if len(faces)>1: return None,{'status':'not_evaluated','reason':'Multiple faces detected','face_count':int(len(faces))}
        face=faces[0]; aligned=self.recognizer.alignCrop(image,face); feature=self.recognizer.feature(aligned); return feature,{'status':'passed','face_count':1}
    def compare(self,document_image:np.ndarray,reference_image:np.ndarray):
        f1,m1=self.embedding(document_image); f2,m2=self.embedding(reference_image)
        if f1 is None or f2 is None: return {'status':'not_evaluated','similarity':None,'document':m1,'reference':m2,'message':'Face comparison could not be evaluated from the supplied images.'}
        cosine=float(self.recognizer.match(f1,f2,cv2.FaceRecognizerSF_FR_COSINE)); l2=float(self.recognizer.match(f1,f2,cv2.FaceRecognizerSF_FR_NORM_L2)); status='passed' if cosine>=0.363 else 'failed'
        return {'status':status,'similarity':cosine,'l2_distance':l2,'document':m1,'reference':m2,'threshold':0.363,'message':'Similarity screening only; it is not a legal identity determination.'}
