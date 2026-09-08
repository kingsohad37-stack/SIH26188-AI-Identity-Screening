'use client'
import { useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import { ShieldCheck, ArrowRight, Loader2 } from 'lucide-react'

export default function Login(){
 const supabase=createClient()
 const [email,setEmail]=useState('')
 const [password,setPassword]=useState('')
 const [loading,setLoading]=useState(false)
 const [googleLoading,setGoogleLoading]=useState(false)
 const [error,setError]=useState('')
 async function submit(e:React.FormEvent){
  e.preventDefault(); setLoading(true); setError('')
  const result=await supabase.auth.signInWithPassword({email,password})
  if(result.error){setError(result.error.message);setLoading(false);return}
  window.location.href='/dashboard'
 }
 async function signInWithGoogle(){
  setGoogleLoading(true); setError('')
  const { error } = await supabase.auth.signInWithOAuth({
   provider:'google',
   options:{ redirectTo:`${window.location.origin}/auth/callback?next=/dashboard` }
  })
  if(error){setError(error.message);setGoogleLoading(false)}
 }
 return <main className="min-h-screen flex items-center justify-center p-6"><div className="w-full max-w-md material rounded-[28px] p-8 md:p-10"><div className="mb-10"><div className="mb-6 flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-black"><ShieldCheck size={25}/></div><p className="text-sm text-white/45">SIH26188</p><h1 className="mt-1 text-3xl font-semibold tracking-[-0.035em]">Secure screening.</h1><p className="mt-2 text-white/55">Sign in to access your screening workspace.</p></div><button type="button" onClick={signInWithGoogle} disabled={googleLoading||loading} className="pressable focus-ring flex w-full items-center justify-center gap-3 rounded-2xl border border-white/10 bg-white/[.045] px-4 py-3.5 font-medium disabled:opacity-60">{googleLoading?<Loader2 className="animate-spin" size={18}/>:<><span className="flex h-5 w-5 items-center justify-center rounded-full bg-white text-xs font-bold text-black">G</span> Continue with Google</>}</button><div className="my-6 flex items-center gap-3"><div className="h-px flex-1 bg-white/10"/><span className="text-xs text-white/35">OR</span><div className="h-px flex-1 bg-white/10"/></div><form onSubmit={submit} className="space-y-4"><label className="block"><span className="mb-2 block text-sm text-white/65">Email</span><input required type="email" value={email} onChange={e=>setEmail(e.target.value)} className="focus-ring w-full rounded-2xl border border-white/10 bg-white/[.045] px-4 py-3.5 outline-none focus:border-white/30"/></label><label className="block"><span className="mb-2 block text-sm text-white/65">Password</span><input required type="password" value={password} onChange={e=>setPassword(e.target.value)} className="focus-ring w-full rounded-2xl border border-white/10 bg-white/[.045] px-4 py-3.5 outline-none focus:border-white/30"/></label>{error&&<p className="rounded-xl bg-red-400/10 px-3 py-2 text-sm text-red-300">{error}</p>}<button disabled={loading||googleLoading} className="pressable focus-ring mt-2 flex w-full items-center justify-center gap-2 rounded-2xl bg-white px-4 py-3.5 font-medium text-black disabled:opacity-60">{loading?<Loader2 className="animate-spin" size={18}/>:<>Continue <ArrowRight size={17}/></>}</button></form></div></main>
}
