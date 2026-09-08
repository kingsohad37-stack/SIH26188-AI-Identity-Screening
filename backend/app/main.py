import os, tempfile
import cv2
import numpy as np
from fastapi import FastAPI, Header, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from .config import settings
from .pipeline import analyze_file
from .face import FaceEngine

app=FastAPI(title='SIH26188 Screening API',version='0.1.0')
app.add_middleware(CORSMiddleware,allow_origins=[settings.allowed_origin],allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
supabase:Client=create_client(settings.supabase_url,settings.supabase_service_role_key); _face_engine=None

def get_face_engine():
 global _face_engine
 if _face_engine is None: _face_engine=FaceEngine()
 return _face_engine

def audit(screening_id,user_id,action,details=None):
 try: supabase.table('audit_events').insert({'screening_id':screening_id,'user_id':user_id,'action':action,'details':details or {}}).execute()
 except Exception: pass

def require_user(authorization):
 if not authorization or not authorization.lower().startswith('bearer '): raise HTTPException(401,'Authentication required')
 try:
  user=supabase.auth.get_user(authorization.split(' ',1)[1].strip()).user
  if not user: raise ValueError()
  return user.id
 except Exception: raise HTTPException(401,'Invalid authentication token')

@app.get('/health')
def health(): return {'ok':True,'service':'sih26188-screening-api','model_version':settings.model_version}

@app.post('/v1/screenings/{screening_id}/analyze')
def analyze(screening_id:str,authorization:str|None=Header(default=None)):
 user_id=require_user(authorization)
 screening=supabase.table('screenings').select('id,user_id,status').eq('id',screening_id).eq('user_id',user_id).single().execute().data
 if not screening: raise HTTPException(404,'Screening not found')
 docs=supabase.table('screening_documents').select('id,storage_path,mime_type,original_filename').eq('screening_id',screening_id).eq('user_id',user_id).limit(1).execute().data
 if not docs: raise HTTPException(404,'Document not found')
 doc=docs[0]; audit(screening_id,user_id,'analysis_started',{'document_id':doc['id']})
 supabase.table('screenings').update({'status':'processing'}).eq('id',screening_id).eq('user_id',user_id).execute()
 supabase.table('screening_documents').update({'analysis_status':'processing'}).eq('id',doc['id']).eq('user_id',user_id).execute()
 local_path=None
 try:
  blob=supabase.storage.from_('screening-documents').download(doc['storage_path'])
  suffix=os.path.splitext(doc['original_filename'])[1] or '.bin'
  with tempfile.NamedTemporaryFile(delete=False,suffix=suffix) as f: f.write(blob); local_path=f.name
  result=analyze_file(local_path,doc['mime_type'])
  supabase.table('screening_documents').update({'analysis_status':'completed','document_type':result['document_type'],'extracted_data':result['extracted_data'],'analysis_metadata':{'model_version':settings.model_version,'forensics':result['forensics'],'forensic_assessment':result['forensic_assessment'],'pages_processed':result['pages_processed'],'processed_at':result['processed_at']}}).eq('id',doc['id']).eq('user_id',user_id).execute()
  checks=[{'screening_id':screening_id,'check_type':'ocr','status':'passed','details':{'pages_processed':result['pages_processed']},'model_version':settings.model_version},{'screening_id':screening_id,'check_type':'mrz_validation','status':result['extracted_data']['validation']['status'],'details':result['extracted_data']['validation'],'model_version':settings.model_version},{'screening_id':screening_id,'check_type':'image_forensics','status':result['forensic_assessment']['status'],'details':{'signals':result['forensics'],'assessment':result['forensic_assessment']},'model_version':settings.model_version}]
  supabase.table('screening_checks').insert(checks).execute()
  severity='high' if result['extracted_data']['validation']['status']=='failed' else ('warning' if result['forensic_assessment']['status']=='suspicious' else 'info')
  code='MRZ_VALIDATION_FAILED' if severity=='high' else ('FORENSIC_REVIEW_SIGNAL' if severity=='warning' else 'BASELINE_ANALYSIS_COMPLETED')
  title='MRZ validation requires review' if severity=='high' else ('Forensic review signal detected' if severity=='warning' else 'Baseline analysis completed')
  description='One or more deterministic MRZ/date checks failed.' if severity=='high' else ('Localized recompression differences were detected; this is not proof of tampering.' if severity=='warning' else 'OCR, MRZ parsing and deterministic image-forensics signals were evaluated. These checks do not establish document authenticity by themselves.')
  finding={'screening_id':screening_id,'severity':severity,'code':code,'title':title,'description':description,'evidence':{'validation':result['extracted_data']['validation'],'forensic_assessment':result['forensic_assessment']}}
  supabase.table('screening_findings').insert(finding).execute(); audit(screening_id,user_id,'analysis_completed',{'document_type':result['document_type']}); supabase.table('screenings').update({'status':'completed','document_type':result['document_type'],'overall_assessment':'inconclusive'}).eq('id',screening_id).eq('user_id',user_id).execute()
  return {'screening_id':screening_id,'status':'completed','document_type':result['document_type'],'extracted_data':result['extracted_data'],'checks':checks,'findings':[finding],'message':'Real baseline analysis completed. Authenticity is not determined by this baseline alone.'}
 except Exception as e:
  try: supabase.table('screening_documents').update({'analysis_status':'failed'}).eq('id',doc['id']).eq('user_id',user_id).execute(); supabase.table('screenings').update({'status':'failed'}).eq('id',screening_id).eq('user_id',user_id).execute()
  except Exception: pass
  audit(screening_id,user_id,'analysis_failed',{'error_type':type(e).__name__}); raise HTTPException(500,'Analysis failed')
 finally:
  if local_path:
   try: os.unlink(local_path)
   except OSError: pass

def recompute_risk(screening_id,user_id):
 rows=supabase.table('screening_checks').select('check_type,status').eq('screening_id',screening_id).execute().data or []; score=0; evaluated=0
 weights={'mrz_validation':{'failed':60,'suspicious':35,'not_evaluated':10},'image_forensics':{'suspicious':25,'failed':40,'not_evaluated':10},'face_verification':{'failed':45,'suspicious':25,'not_evaluated':10}}
 for r in rows:
  if r['status'] in ('passed','failed','suspicious'): evaluated+=1
  score+=weights.get(r['check_type'],{}).get(r['status'],0)
 score=min(100,score); assessment='low_risk' if score<25 else ('medium_risk' if score<60 else 'high_risk')
 if evaluated==0: assessment='not_evaluated'
 supabase.table('screenings').update({'risk_score':score,'overall_assessment':assessment}).eq('id',screening_id).eq('user_id',user_id).execute(); return score,assessment

@app.post('/v1/screenings/{screening_id}/face-verify')
async def face_verify(screening_id:str,reference:UploadFile=File(...),authorization:str|None=Header(default=None)):
 user_id=require_user(authorization); audit(screening_id,user_id,'face_verification_started')
 screening=supabase.table('screenings').select('id,user_id').eq('id',screening_id).eq('user_id',user_id).single().execute().data
 if not screening: raise HTTPException(404,'Screening not found')
 docs=supabase.table('screening_documents').select('id,storage_path').eq('screening_id',screening_id).eq('user_id',user_id).limit(1).execute().data
 if not docs: raise HTTPException(404,'Document not found')
 try:
  ref_bytes=await reference.read()
  if len(ref_bytes)>10*1024*1024: raise HTTPException(413,'Reference image is too large')
  ref_img=cv2.imdecode(np.frombuffer(ref_bytes,np.uint8),cv2.IMREAD_COLOR); doc_bytes=supabase.storage.from_('screening-documents').download(docs[0]['storage_path']); doc_img=cv2.imdecode(np.frombuffer(doc_bytes,np.uint8),cv2.IMREAD_COLOR)
  result={'status':'not_evaluated','message':'One or both images could not be decoded.'} if doc_img is None or ref_img is None else get_face_engine().compare(doc_img,ref_img)
  check_status=result.get('status','not_evaluated'); supabase.table('screening_checks').insert({'screening_id':screening_id,'check_type':'face_verification','status':check_status,'score':result.get('similarity'),'details':result,'model_version':'opencv-yunet-sface-0.1'}).execute(); risk_score,assessment=recompute_risk(screening_id,user_id)
  finding=None
  if check_status=='failed': finding={'screening_id':screening_id,'severity':'high','code':'FACE_SIMILARITY_MISMATCH','title':'Face similarity mismatch','description':'The supplied reference face did not reach the screening similarity threshold. This is a review signal, not proof of impersonation.','evidence':result}
  elif check_status=='not_evaluated': finding={'screening_id':screening_id,'severity':'warning','code':'FACE_NOT_EVALUATED','title':'Face verification not evaluated','description':result.get('message','Face verification could not be evaluated.'),'evidence':result}
  if finding: supabase.table('screening_findings').insert(finding).execute()
  audit(screening_id,user_id,'face_verification_completed',{'status':check_status}); return {'screening_id':screening_id,'status':check_status,'result':result,'finding':finding,'risk_score':risk_score,'overall_assessment':assessment}
 except HTTPException: raise
 except Exception as e: raise HTTPException(500,f'Face verification failed: {type(e).__name__}')
