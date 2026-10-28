"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { api } from "@/lib/api"
import { User } from "@/types/api"
import { formatCurrency } from "@/lib/utils"

export { formatCurrency }

export function useAuth() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [token, setTokenState] = useState<string | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const router = useRouter()

  useEffect(() => {
    const storedToken = localStorage.getItem("access_token")
    if (storedToken) {
      setTokenState(storedToken)
      setIsAuthenticated(true)
      api.setToken(storedToken)
      fetchUser(storedToken)
    } else {
      setLoading(false)
    }
  }, [])

  const fetchUser = async (accessToken: string) => {
    try {
      const res = await api.get<User>("/auth/me")
      setUser(res)
    } catch (err) {
      console.error("Failed to fetch user:", err)
      logout()
    } finally {
      setLoading(false)
    }
  }

  const login = async (accessToken: string, refreshToken?: string) => {
    localStorage.setItem("access_token", accessToken)
    if (refreshToken) localStorage.setItem("refresh_token", refreshToken)
    api.setToken(accessToken)
    setTokenState(accessToken)
    setIsAuthenticated(true)
    await fetchUser(accessToken)
  }

  const logout = () => {
    localStorage.removeItem("access_token")
    localStorage.removeItem("refresh_token")
    api.setToken(null)
    setTokenState(null)
    setIsAuthenticated(false)
    setUser(null)
    router.push("/login")
  }

  const requireAuth = () => {
    if (!loading && !isAuthenticated) {
      router.push("/login")
    }
    return { user, loading, token, isAuthenticated }
  }

  return { user, loading, token, login, logout, requireAuth, isAuthenticated }
}
