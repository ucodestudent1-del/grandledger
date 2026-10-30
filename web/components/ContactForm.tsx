"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { api } from "@/lib/api"
import { useAuth } from "@/app/hooks/useAuth"
import { Contact } from "@/types/api"
import { Save, Trash2 } from "lucide-react"

interface ContactFormProps {
  contactType: "customer" | "vendor"
  contactId?: string
}

export default function ContactForm({ contactType, contactId }: ContactFormProps) {
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [contact, setContact] = useState<Contact | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const router = useRouter()

  const isEdit = !!contactId
  const [formData, setFormData] = useState({
    name: "",
    type: contactType,
    email: "",
    phone: "",
    address: "",
  })

  useEffect(() => {
    if (!isAuthenticated) return
    if (contactId) {
      api.get<Contact>(`/contacts/${contactId}`)
        .then((res) => {
          setContact(res)
          setFormData({
            name: res.name,
            type: res.type,
            email: res.email || "",
            phone: res.phone || "",
            address: JSON.stringify(res.address || {}, null, 2),
          })
        })
        .catch(console.error)
    }
  }, [isAuthenticated, contactId])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      const payload: any = {
        name: formData.name,
        type: formData.type,
        email: formData.email || undefined,
        phone: formData.phone || undefined,
      }
      if (formData.address) {
        try {
          payload.address = JSON.parse(formData.address)
        } catch {
          console.warn("Invalid JSON in address field, skipping")
        }
      }

      if (isEdit) {
        await api.patch(`/contacts/${contactId}`, payload)
      } else {
        await api.post("/contacts", payload)
      }
      router.push(contactType === "customer" ? "/customers" : "/vendors")
    } catch (err: any) {
      setError(err.detail || "Failed to save contact")
    } finally {
      setSaving(false)
    }
  }

  if (authLoading) return <div className="p-6">Loading...</div>
  if (!isAuthenticated) return null

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">
        {isEdit ? `Edit ${contact?.name || ""}` : `New ${contactType === "customer" ? "Customer" : "Vendor"}`}
      </h1>

      {error && <p className="text-sm text-destructive">{error}</p>}

      <form onSubmit={handleSubmit} className="space-y-4 max-w-2xl">
        <div>
          <label className="block text-sm font-medium">Name *</label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="mt-1 block w-full rounded-md border border-input px-3 py-2 bg-background"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium">Email</label>
          <input
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            className="mt-1 block w-full rounded-md border border-input px-3 py-2 bg-background"
          />
        </div>
        <div>
          <label className="block text-sm font-medium">Phone</label>
          <input
            type="tel"
            value={formData.phone}
            onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
            className="mt-1 block w-full rounded-md border border-input px-3 py-2 bg-background"
          />
        </div>
        <div>
          <label className="block text-sm font-medium">Address (JSON)</label>
          <textarea
            value={formData.address}
            onChange={(e) => setFormData({ ...formData, address: e.target.value })}
            className="mt-1 block w-full rounded-md border border-input px-3 py-2 bg-background"
            rows={3}
            placeholder='{"street": "123 Main St", "city": "New York", "state": "NY", "zip": "10001"}'
          />
        </div>
        <div className="flex gap-2">
          <button
            type="submit"
            disabled={saving}
            className="bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm disabled:opacity-50 flex items-center gap-2"
          >
            <Save className="h-4 w-4" />
            {saving ? "Saving..." : isEdit ? "Update" : "Create"}
          </button>
          <button
            type="button"
            onClick={() => router.push(contactType === "customer" ? "/customers" : "/vendors")}
            className="border border-input px-4 py-2 rounded text-sm"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  )
}
