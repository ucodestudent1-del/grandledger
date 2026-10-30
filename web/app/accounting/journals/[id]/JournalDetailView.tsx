"use client"

import { useParams, useRouter } from "next/navigation"
import JournalForm from "@/components/JournalForm"
import { useAuth } from "@/app/hooks/useAuth"

export default function JournalDetailView() {
  const params = useParams<{ id: string }>()
  const router = useRouter()
  const { isAuthenticated, loading: authLoading } = useAuth()

  if (authLoading) return <div className="p-6">Loading...</div>
  if (!isAuthenticated) return null

  const journalId = params?.id || ""

  return (
    <div className="space-y-4">
      <button
        onClick={() => router.back()}
        className="text-sm text-muted-foreground hover:text-foreground"
      >
        Back
      </button>
      <JournalForm journalId={journalId} />
    </div>
  )
}
