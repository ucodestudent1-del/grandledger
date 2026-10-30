"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { useAuth } from "@/app/hooks/useAuth"
import { Company, User } from "@/types/api"
import { Save, Lock, Unlock } from "lucide-react"
import StatusBadge from "@/components/ui/StatusBadge"

export default function CompanySettingsPage() {
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [company, setCompany] = useState<Company | null>(null)
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [lockingPeriod, setLockingPeriod] = useState(false)
  const [periodLockDate, setPeriodLockDate] = useState("")
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
          if (companies[0].locked_period_end) {
            setPeriodLockDate(companies[0].locked_period_end.split("T")[0])
          }
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

  const handlePeriodLock = async (lock: boolean) => {
    if (!company) return
    setLockingPeriod(true)
    try {
      const payload = lock ? { locked_period_end: periodLockDate } : { locked_period_end: null }
      const updated = await api.patch<Company>(`/companies/${company.id}/period-lock`, payload)
      setCompany(updated)
    } catch (err: any) {
      console.error("Failed to update period lock:", err)
    } finally {
      setLockingPeriod(false)
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

      <div className="border rounded-lg p-6 space-y-4">
        <h2 className="text-lg font-semibold">Period Locking</h2>
        <p className="text-sm text-muted-foreground">
          Lock accounting periods to prevent changes to closed periods. Once locked, journal entries
          on or before the lock date cannot be modified.
        </p>

        {company?.locked_period_end ? (
          <div className="flex items-center gap-4">
            <StatusBadge status="void">Period Locked</StatusBadge>
            <span className="text-sm">
              Locked through: {new Date(company.locked_period_end).toLocaleDateString()}
            </span>
            <button
              onClick={() => handlePeriodLock(false)}
              disabled={lockingPeriod}
              className="border border-input px-3 py-1 rounded text-sm flex items-center gap-1"
            >
              <Unlock className="h-3 w-3" />
              {lockingPeriod ? "Unlocking..." : "Unlock Period"}
            </button>
          </div>
        ) : (
          <div className="flex items-end gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Lock Through Date</label>
              <input
                type="date"
                value={periodLockDate}
                onChange={(e) => setPeriodLockDate(e.target.value)}
                className="rounded-md border border-input px-3 py-2 bg-background"
              />
            </div>
            <button
              onClick={() => handlePeriodLock(true)}
              disabled={lockingPeriod || !periodLockDate}
              className="border border-input px-3 py-1 rounded text-sm flex items-center gap-1 mb-[2px]"
            >
              <Lock className="h-3 w-3" />
              {lockingPeriod ? "Locking..." : "Lock Period"}
            </button>
          </div>
        )}
      </div>

      <div className="border rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-3">Team Members</h2>
        <p className="text-sm text-muted-foreground mb-3">
          Current users: {users.length}
        </p>
      </div>
    </div>
  )
}
