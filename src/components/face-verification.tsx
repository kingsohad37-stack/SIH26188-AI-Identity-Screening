'use client'
import { useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import { Loader2, ScanFace } from 'lucide-react'

export function FaceVerification({ screeningId }: { screeningId: string }) {
  const [file, setFile] = useState<File | null>(null); const [busy, setBusy] = useState(false); const [result, setResult] = useState<string>(''); const [error, setError] = useState('')
  async function verify() {
    if (!file) return; setBusy(true); setError(''); setResult(''); const supabase = createClient(); const { data: { session } } = await supabase.auth.getSession(); const api = process.env.NEXT_PUBLIC_SCREENING_API_URL
    if (!api || !session) { setError('Screening API or session is unavailable.'); setBusy(false); return }
    const form = new FormData(); form.append('reference', file); const response = await fetch(`${api}/v1/screenings/${screeningId}/face-verify`, { method: 'POST', headers: { Authorization: `Bearer ${session.access_token}` }, body: form }); const body = await response.json().catch(() => ({}))
    if (!response.ok) setError(body.detail || 'Face verification failed.')
    else setResult(body.result?.status === 'passed' ? 'Face similarity passed the screening threshold.' : body.result?.status === 'failed' ? 'Face similarity did not pass the screening threshold.' : 'Face verification was not evaluated.')
    setBusy(false); if (response.ok) window.location.reload()
  }
  return <section className="material-soft mt-4 rounded-2xl p-5"><div className="flex items-center gap-2"><ScanFace size={18} className="text-white/60"/><h2 className="font-medium">Face verification</h2></div><p className="mt-2 text-sm leading-6 text-white/40">Provide a separate reference photo containing one face. The system compares facial embeddings against the document image when a usable portrait can be detected. This is similarity screening, not legal identity determination.</p><label className="pressable mt-4 block cursor-pointer rounded-xl border border-dashed border-white/15 bg-white/[.025] p-4"><input type="file" accept="image/jpeg,image/png,image/webp" className="sr-only" onChange={e=>setFile(e.target.files?.[0]||null)}/><span className="text-sm text-white/60">{file ? file.name : 'Choose reference face photo'}</span></label>{error&&<p className="mt-3 text-sm text-red-300">{error}</p>}{result&&<p className="mt-3 text-sm text-white/60">{result}</p>}<button disabled={!file||busy} onClick={verify} className="pressable focus-ring mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-white px-4 py-3 text-sm font-medium text-black disabled:opacity-40">{busy?<><Loader2 size={16} className="animate-spin"/>Comparing…</>:'Run face verification'}</button></section>
}
