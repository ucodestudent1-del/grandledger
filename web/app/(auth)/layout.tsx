"use client"

import { ThemeProvider } from "next-themes"
import { Toaster } from "@/components/ui/sonner"
import "@/styles/globals.css"

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <ThemeProvider attribute="class" defaultTheme="light">
      <main className="min-h-screen bg-muted flex items-center justify-center">
        {children}
      </main>
      <Toaster />
    </ThemeProvider>
  )
}
