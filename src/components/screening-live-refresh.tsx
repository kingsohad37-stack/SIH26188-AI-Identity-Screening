'use client'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export function ScreeningLiveRefresh({ status }: { status: string | null }) {
 const router = useRouter()
 useEffect(() => {
  if (status !== 'processing' && status !== 'created') return
  const timer = window.setInterval(() => router.refresh(), 750)
  return () => window.clearInterval(timer)
 }, [status, router])
 return null
}
