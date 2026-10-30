"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { useAuth } from "@/app/hooks/useAuth"
import { Account } from "@/types/api"
import { Plus, Edit } from "lucide-react"

const accountTypes = [
  { value: "asset", label: "Asset" },
  { value: "liability", label: "Liability" },
  { value: "equity", label: "Equity" },
  { value: "revenue", label: "Revenue" },
  { value: "expense", label: "Expense" },
]

export default function ChartOfAccountsPage() {
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [accounts, setAccounts] = useState<Account[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingAccount, setEditingAccount] = useState<Account | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const [formData, setFormData] = useState({
    code: "",
    name: "",
    type: "asset",
  })

  useEffect(() => {
    if (!isAuthenticated) return
    api.get<Account[]>("/accounts")
      .then(setAccounts)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [isAuthenticated])

  const handleEdit = (account: Account) => {
    setEditingAccount(account)
    setFormData({ code: account.code, name: account.name, type: account.type })
    setShowForm(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      if (editingAccount) {
        await api.patch(`/accounts/${editingAccount.id}`, formData)
      } else {
        await api.post("/accounts", formData)
      }
      const res = await api.get<Account[]>("/accounts")
      setAccounts(res)
      setShowForm(false)
      setEditingAccount(null)
      setFormData({ code: "", name: "", type: "asset" })
    } catch (err: any) {
      setError(err.detail || "Failed to save account")
    } finally {
      setSaving(false)
    }
  }

  const handleNew = () => {
    setEditingAccount(null)
    setFormData({ code: "", name: "", type: "asset" })
    setShowForm(true)
  }

  if (authLoading) return <div className="p-6">Loading...</div>
  if (!isAuthenticated) return null
  if (loading) return <div className="p-6">Loading chart of accounts...</div>

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Chart of Accounts</h1>
        <button
          onClick={handleNew}
          className="bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          Add Account
        </button>
      </div>

      {showForm && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-card border rounded-lg p-6 max-w-md w-full">
            <h2 className="text-xl font-bold mb-4">
              {editingAccount ? "Edit Account" : "New Account"}
            </h2>
            {error && <p className="text-sm text-destructive mb-4">{error}</p>}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium">Code *</label>
                <input
                  type="text"
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                  className="mt-1 block w-full rounded-md border border-input px-3 py-2 bg-background"
                  required
                />
              </div>
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
                <label className="block text-sm font-medium">Type *</label>
                <select
                  value={formData.type}
                  onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                  className="mt-1 block w-full rounded-md border border-input px-3 py-2 bg-background"
                >
                  {accountTypes.map((t) => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </div>
              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={saving}
                  className="bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm disabled:opacity-50"
                >
                  {saving ? "Saving..." : "Save"}
                </button>
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="border border-input px-4 py-2 rounded text-sm"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="border rounded-lg overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-muted">
              <th className="text-left p-3">Code</th>
              <th className="text-left p-3">Name</th>
              <th className="text-left p-3">Type</th>
              <th className="text-center p-3">System</th>
              <th className="text-right p-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {accounts.length === 0 ? (
              <tr>
                <td colSpan={5} className="p-4 text-center text-muted-foreground">
                  No accounts found.
                </td>
              </tr>
            ) : (
              accounts.map((acct) => (
                <tr key={acct.id} className="border-t">
                  <td className="p-3 font-mono">{acct.code}</td>
                  <td className="p-3">{acct.name}</td>
                  <td className="p-3 capitalize">{acct.type}</td>
                  <td className="p-3 text-center">{acct.is_system ? "Yes" : "No"}</td>
                  <td className="p-3 text-right">
                    {!acct.is_system && (
                      <button
                        onClick={() => handleEdit(acct)}
                        className="text-sm text-primary hover:underline"
                      >
                        Edit
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
