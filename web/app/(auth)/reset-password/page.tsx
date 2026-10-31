"use client"

import { useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { api } from "@/lib/api"

export default function ResetPasswordPage() {
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()
  const searchParams = useSearchParams()
  const token = searchParams.get("token")

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (password !== confirmPassword) {
      setError("Passwords do not match")
      return
    }
    if (!token) {
      setError("Invalid reset token")
      return
    }
    setIsLoading(true)
    setError(null)
    try {
      await api.post("/auth/reset-password", { token, new_password: password })
      router.push("/login")
    } catch (err: any) {
      setError(err.detail || "An error occurred")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-md space-y-4 p-8 border rounded-lg shadow-lg"
      >
        <h1 className="text-2xl font-bold">Reset password</h1>

        {error && (
          <p className="text-sm text-destructive">{error}</p>
        )}

        <input
          type="password"
          placeholder="New password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          minLength={8}
          className="w-full px-3 py-2 border rounded-md"
        />

        <input
          type="password"
          placeholder="Confirm new password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          required
          minLength={8}
          className="w-full px-3 py-2 border rounded-md"
        />

        <button
          type="submit"
          disabled={isLoading || !token}
          className="w-full px-3 py-2 bg-primary text-primary-foreground rounded-md disabled:opacity-50"
        >
          {isLoading ? "Resetting..." : "Reset password"}
        </button>
      </form>
    </div>
  )
}
