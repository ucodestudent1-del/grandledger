"use client"

import { useParams, useRouter } from "next/navigation"
import InvoiceForm from "@/components/InvoiceForm"
import { useAuth } from "@/app/hooks/useAuth"

export default function InvoiceDetailView() {
  const params = useParams<{ id: string }>()
  const router = useRouter()
  const { isAuthenticated, loading: authLoading } = useAuth()

  if (authLoading) return <div className="p-6">Loading...</div>
  if (!isAuthenticated) return null

  const invoiceId = params?.id || ""

  return (
    <div className="space-y-4">
      <button
        onClick={() => router.back()}
        className="text-sm text-muted-foreground hover:text-foreground"
      >
        Back
      </button>
      <InvoiceForm invoiceId={invoiceId} />
    </div>
  )
}
