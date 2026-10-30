"use client"

import { useParams, useRouter } from "next/navigation"
import BillForm from "@/components/BillForm"
import { useAuth } from "@/app/hooks/useAuth"

export default function BillDetailView() {
  const params = useParams<{ id: string }>()
  const router = useRouter()
  const { isAuthenticated, loading: authLoading } = useAuth()

  if (authLoading) return <div className="p-6">Loading...</div>
  if (!isAuthenticated) return null

  const billId = params?.id || ""

  return (
    <div className="space-y-4">
      <button
        onClick={() => router.back()}
        className="text-sm text-muted-foreground hover:text-foreground"
      >
        Back
      </button>
      <BillForm billId={billId} />
    </div>
  )
}
