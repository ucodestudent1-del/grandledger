"use client"

import { usePathname, useRouter } from "next/navigation"
import { useEffect } from "react"
import { useAuth } from "@/app/hooks/useAuth"
import Sidebar from "@/components/Sidebar"
import Header from "@/components/Header"

export default function ClientProviders({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const router = useRouter()
  const { isAuthenticated, loading: authLoading } = useAuth()

  const isAuthPage = pathname.startsWith("/login") || pathname.startsWith("/signup")

  useEffect(() => {
    if (!authLoading && !isAuthenticated && !isAuthPage) {
      router.replace("/login")
    }
  }, [isAuthenticated, authLoading, isAuthPage, router])

  if (authLoading && !isAuthPage) return <div className="p-6">Loading...</div>

  return (
    <>
      {isAuthenticated && !isAuthPage ? (
        <div className="flex h-screen overflow-hidden">
          <Sidebar />
          <div className="flex-1 flex flex-col overflow-hidden">
            <Header />
            <main className="flex-1 overflow-y-auto bg-background p-6">
              {children}
            </main>
          </div>
        </div>
      ) : (
        children
      )}
    </>
  )
}
