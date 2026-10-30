"use client"

import { useParams, useRouter } from "next/navigation"
import VendorForm from "@/components/VendorForm"
import { useAuth } from "@/app/hooks/useAuth"

export default function VendorDetailView() {
  const params = useParams<{ id: string }>()
  const router = useRouter()
  const { isAuthenticated, loading: authLoading } = useAuth()

  if (authLoading) return <div className="p-6">Loading...</div>
  if (!isAuthenticated) return null

  const vendorId = params?.id || ""

  return (
    <div className="space-y-4">
      <button
        onClick={() => router.back()}
        className="text-sm text-muted-foreground hover:text-foreground"
      >
        Back
      </button>
      <VendorForm vendorId={vendorId} />
    </div>
  )
}
