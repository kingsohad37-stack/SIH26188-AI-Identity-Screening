'use client'
import Link from 'next/link'
import { FileCheck2, LayoutDashboard, Plus, History, LogOut } from 'lucide-react'
import { createClient } from '@/lib/supabase/client'

export function Sidebar(){
 const supabase=createClient();
 async function signOut(){await supabase.auth.signOut();window.location.href='/auth/login'}
 return <aside className="material sticky top-4 hidden h-[calc(100vh-2rem)] w-[250px] shrink-0 rounded-[28px] p-3 md:flex md:flex-col"><div className="px-3 py-4"><div className="flex items-center gap-3"><div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white text-black"><FileCheck2 size={18}/></div><div><div className="font-semibold tracking-[-.02em]">Sentinel</div><div className="text-xs text-white/35">SIH26188</div></div></div></div><nav className="mt-4 space-y-1"><Link className="pressable flex items-center gap-3 rounded-xl bg-white/[.08] px-3 py-2.5 text-sm" href="/dashboard"><LayoutDashboard size={17}/>Overview</Link><Link className="pressable flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-white/60 hover:bg-white/[.05] hover:text-white" href="/screenings/new"><Plus size={17}/>New screening</Link><Link className="pressable flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-white/60 hover:bg-white/[.05] hover:text-white" href="/screenings"><History size={17}/>Screening history</Link></nav><div className="mt-auto"><button onClick={signOut} className="pressable flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-white/50 hover:bg-white/[.05] hover:text-white"><LogOut size={17}/>Sign out</button></div></aside>
}
