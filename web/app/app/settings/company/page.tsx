"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { useAuth } from "@/app/hooks/useAuth"
import { Company, User } from "@/types/api"
import { Save } from "lucide-react"

export default function CompanySettingsPage() {
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [company, setCompany] = useState<Company | null>(null)
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [editForm, setEditForm] = useState({ name: "", currency: "USD", financial_year_start: "" })

  useEffect(() => {
    if (!isAuthenticated) return
    const fetchData = async () => {
      try {
        const [companies, usersRes] = await Promise.all([
          api.get<Company[]>("/companies"),
          api.get<User[]>("/users").catch(() => []),
        ])
        if (companies.length > 0) {
          setCompany(companies[0])
          setEditForm({
            name: companies[0].name,
            currency: companies[0].currency,
            financial_year_start: companies[0].financial_year_start || "",
          })
        }
        setUsers(usersRes || [])
      } catch (err) {
        console.error("Failed to fetch data:", err)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [isAuthenticated])

  const handleSave = async () => {
    if (!company) return
    setSaving(true)
    try {
      await api.patch<Company>(`/companies/${company.id}`, editForm)
      setCompany({ ...company, ...editForm })
    } catch (err: any) {
      console.error("Failed to save:", err)
    } finally {
      setSaving(false)
    }
  }

  if (authLoading) return <div className="p-6">Loading...</div>
  if (!isAuthenticated) return null
  if (loading) return <div className="p-6">Loading settings...</div>

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Company Settings</h1>

      {company && (
        <div className="border rounded-lg p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium">Name</label>
            <input
              type="text"
              value={editForm.name}
              onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
              className="mt-1 block w-full rounded-md border border-input px-3 py-2 bg-background"
            />
          </div>
          <div>
            <label className="block text-sm font-medium">Currency</label>
            <input
              type="text"
              value={editForm.currency}
              onChange={(e) => setEditForm({ ...editForm, currency: e.target.value })}
              className="mt-1 block w-full rounded-md border border-input px-3 py-2 bg-background"
            />
          </div>
          <div>
            <label className="block text-sm font-medium">Financial Year Start</label>
            <input
              type="date"
              value={editForm.financial_year_start}
              onChange={(e) => setEditForm({ ...editForm, financial_year_start: e.target.value })}
              className="mt-1 block w-full rounded-md border border-input px-3 py-2 bg-background"
            />
          </div>
          <div>
            <label className="block text-sm font-medium">Slug</label>
            <p className="mt-1 text-sm text-muted-foreground">{company.slug}</p>
          </div>

          <button
            onClick={handleSave}
            disabled={saving}
            className="bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm flex items-center gap-2"
          >
            <Save className="h-4 w-4" />
            {saving ? "Saving..." : "Save Changes"}
          </button>
        </div>
      )}

      <div className="border rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-3">Team Members</h2>
        <p className="text-sm text-muted-foreground mb-3">
          Current users: {users.length}
        </p>
      </div>
    </div>
  )
}
