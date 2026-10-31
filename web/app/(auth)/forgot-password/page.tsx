"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { api } from "@/lib/api"

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("")
  const [isSubmitted, setIsSubmitted] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError(null)
    try {
      await api.post("/auth/forgot-password", { email })
      setIsSubmitted(true)
    } catch (err: any) {
      setError(err.detail || "An error occurred")
    } finally {
      setIsLoading(false)
    }
  }

  if (isSubmitted) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="w-full max-w-md space-y-4 p-8 border rounded-lg shadow-lg">
          <h1 className="text-2xl font-bold">Check your email</h1>
          <p className="text-sm text-muted-foreground">
            If an account exists for {email}, a password reset link has been sent.
          </p>
          <button
            onClick={() => router.push("/login")}
            className="text-sm text-primary hover:underline"
          >
            Back to login
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen items-center justify-center">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-md space-y-4 p-8 border rounded-lg shadow-lg"
      >
        <h1 className="text-2xl font-bold">Forgot password?</h1>
        <p className="text-sm text-muted-foreground">
          Enter your email to receive a password reset link.
        </p>

        {error && (
          <p className="text-sm text-destructive">{error}</p>
        )}

        <input
          type="email"
          placeholder="you@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className="w-full px-3 py-2 border rounded-md"
        />

        <button
          type="submit"
          disabled={isLoading}
          className="w-full px-3 py-2 bg-primary text-primary-foreground rounded-md disabled:opacity-50"
        >
          {isLoading ? "Sending..." : "Send reset link"}
        </button>

        <button
          type="button"
          onClick={() => router.push("/login")}
          className="text-sm text-primary hover:underline"
        >
          Back to login
        </button>
      </form>
    </div>
  )
}
