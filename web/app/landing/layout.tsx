import type { ReactNode } from "react"
import "@/styles/globals.css"

export const metadata = {
  title: "GrandLedger — Bookkeeping SaaS",
  description:
    "Multi-tenant double-entry bookkeeping for freelancers, small businesses, and accountants.",
}

export default function LandingLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>{children}</body>
    </html>
  )
}
