import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = { title: 'Sentinel — Document Screening', description: 'AI-assisted identity document screening system.' }
export default function RootLayout({ children }: Readonly<{children: React.ReactNode}>) { return <html lang="en"><body>{children}</body></html> }
