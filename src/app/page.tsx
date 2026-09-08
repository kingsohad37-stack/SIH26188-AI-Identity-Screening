import Link from 'next/link'
import { ScanLine, ShieldCheck } from 'lucide-react'

export default function Home(){
 return <main className="flex min-h-screen items-center justify-center bg-white px-5 text-neutral-900"><section className="w-full max-w-md text-center"><div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-black text-white"><ScanLine size={26}/></div><h1 className="mt-6 text-3xl font-semibold tracking-[-.04em]">Document Screening</h1><p className="mt-2 text-neutral-500">AI-assisted identity and document authenticity checks.</p><Link href="/screenings/new" className="pressable focus-ring mt-8 inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-black px-6 py-4 font-medium text-white"><ScanLine size={19}/> Scan document</Link><div className="mt-5 flex items-center justify-center gap-2 text-xs text-neutral-400"><ShieldCheck size={14}/> Secure upload · Audit logged</div></section></main>
}
