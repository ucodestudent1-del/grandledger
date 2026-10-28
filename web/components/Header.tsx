"use client"

import { useRouter } from "next/navigation"
import { useEffect } from "react"
import { api } from "@/lib/api"

export default function Header() {
  const router = useRouter()

  const handleLogout = () => {
    api.setToken(null)
    localStorage.removeItem("access_token")
    router.push("/login")
  }

  return (
    <header className="flex items-center justify-end p-4 border-b bg-card">
      <button
        onClick={handleLogout}
        className="text-sm text-muted-foreground hover:text-foreground"
      >
        Logout
      </button>
    </header>
  )
}
