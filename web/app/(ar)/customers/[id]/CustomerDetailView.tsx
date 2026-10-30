"use client"

import { useParams, useRouter } from "next/navigation"
import ContactForm from "@/components/ContactForm"
import { useAuth } from "@/app/hooks/useAuth"

export default function CustomerDetailView() {
  const params = useParams<{ id: string }>()
  const router = useRouter()
  const { isAuthenticated, loading: authLoading } = useAuth()

  if (authLoading) return <div className="p-6">Loading...</div>
  if (!isAuthenticated) return null

  const contactId = params?.id || ""

  return (
    <div className="space-y-4">
      <button
        onClick={() => router.back()}
        className="text-sm text-muted-foreground hover:text-foreground"
      >
        Back
      </button>
      <ContactForm contactType="customer" contactId={contactId} />
    </div>
  )
}
