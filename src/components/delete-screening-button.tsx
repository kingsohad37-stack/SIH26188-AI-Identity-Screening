'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Trash2, Loader2 } from 'lucide-react'
import { createClient } from '@/lib/supabase/client'

export function DeleteScreeningButton({ screeningId }: { screeningId: string }) {
  const router = useRouter()
  const supabase = createClient()
  const [busy, setBusy] = useState(false)

  async function remove() {
    if (busy || !window.confirm('Delete this screening and its uploaded document? This cannot be undone.')) return
    setBusy(true)
    const { data: docs } = await supabase.from('screening_documents').select('storage_path').eq('screening_id', screeningId)
    const paths = (docs ?? []).map(d => d.storage_path).filter(Boolean)
    if (paths.length) await supabase.storage.from('screening-documents').remove(paths)
    const { error } = await supabase.from('screenings').delete().eq('id', screeningId)
    if (error) {
      window.alert(error.message)
      setBusy(false)
      return
    }
    router.refresh()
  }

  return (
    <button type="button" aria-label="Delete screening" title="Delete screening" disabled={busy} onClick={e => { e.preventDefault(); e.stopPropagation(); remove() }} className="pressable focus-ring inline-flex h-9 w-9 items-center justify-center rounded-xl text-neutral-400 hover:bg-red-50 hover:text-red-600 disabled:opacity-40">
      {busy ? <Loader2 size={16} className="animate-spin" /> : <Trash2 size={16} />}
    </button>
  )
}
