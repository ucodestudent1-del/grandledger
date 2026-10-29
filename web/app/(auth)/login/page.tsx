"use client"

import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import { Loader2 } from "lucide-react"
import { api } from "@/lib/api"
import { useAuth } from "@/app/hooks/useAuth"

const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || ""

export default function LoginPage() {
  const [email, setEmail] = useState("demo@grandledger.com")
  const [password, setPassword] = useState("password123")
  const [isLoading, setIsLoading] = useState(false)
  const [isGoogleLoading, setIsGoogleLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { login } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (GOOGLE_CLIENT_ID && typeof window !== "undefined" && !window.google) {
      const script = document.createElement("script")
      script.src = "https://accounts.google.com/gsi/client"
      script.async = true
      script.defer = true
      script.onload = () => {
        if (window.google) {
          window.google.accounts.id.initialize({
            client_id: GOOGLE_CLIENT_ID,
            callback: handleGoogleCallback,
          })
          window.google.accounts.id.renderButton(
            document.getElementById("google-signin-button"),
            { theme: "outline", size: "large", text: "signin_with", shape: "rectangular" },
          )
        }
      }
      document.head.appendChild(script)
    }
  }, [])

  const handleGoogleCallback = async (response: { credential: string }) => {
    setIsGoogleLoading(true)
    setError(null)
    try {
      const res = await api.post<{ access_token: string; refresh_token: string }>(
        "/auth/google",
        { id_token: response.credential },
      )
      login(res.access_token, res.refresh_token)
      router.push("/")
    } catch (err: any) {
      setError(err.detail || err.message || "Google login failed")
    } finally {
      setIsGoogleLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError(null)
    try {
      const res = await api.post<{ access_token: string; refresh_token: string }>("/auth/login", {
        email,
        password,
      })
      login(res.access_token, res.refresh_token)
      router.push("/")
    } catch (err: any) {
      setError(err.detail || err.message || "Login failed")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <>
      <div className="text-center">
        <h1 className="text-3xl font-bold">GrandLedger</h1>
        <p className="text-sm text-muted-foreground">Sign in to your account</p>
      </div>
      {error && <p className="text-sm text-destructive">{error}</p>}
      {GOOGLE_CLIENT_ID && (
        <div id="google-signin-button" className="w-full flex justify-center"></div>
      )}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium">Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 block w-full rounded-md border border-input px-3 py-2 bg-background"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium">Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 block w-full rounded-md border border-input px-3 py-2 bg-background"
            required
          />
        </div>
        <button
          type="submit"
          disabled={isLoading}
          className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Signing in...
            </>
          ) : (
            "Sign In"
          )}
        </button>
      </form>
      <p className="text-center text-sm text-muted-foreground">
        No account?{" "}
        <a href="/signup" className="text-primary hover:underline">
          Sign up
        </a>
      </p>
    </>
  )
}
