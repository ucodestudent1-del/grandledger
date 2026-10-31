"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { api } from "@/lib/api"
import { useAuth } from "@/app/hooks/useAuth"
import { Account, JournalEntry } from "@/types/api"
import { Save, Trash2, Loader2, Plus, FileDown } from "lucide-react"
import StatusBadge from "@/components/ui/StatusBadge"

interface AccountOption {
  id: string
  code: string
  name: string
  type: string
}

interface JournalLineForm {
  account_id: string
  description: string
  debit: string
  credit: string
}

export default function JournalForm({ journalId }: { journalId?: string }) {
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [journal, setJournal] = useState<JournalEntry | null>(null)
  const [accounts, setAccounts] = useState<AccountOption[]>([])
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  const isEdit = !!journalId
  const [formData, setFormData] = useState<{
    entry_date: string
    description: string
    lines: JournalLineForm[]
  }>(() => ({
    entry_date: new Date().toISOString().split("T")[0],
    description: "",
    lines: [],
  }))

  useEffect(() => {
    if (!isAuthenticated) return
    let mounted = true
    const fetchData = async () => {
      try {
        const accountsRes = await api.get<AccountOption[]>("/accounts")
        if (mounted) setAccounts(accountsRes)
      } catch (err) {
        console.error("Failed to fetch accounts:", err)
      }
    }
    fetchData()
    return () => { mounted = false }
  }, [isAuthenticated])

  useEffect(() => {
    if (!isAuthenticated || !journalId) return
    setLoading(true)
    api.get<JournalEntry>(`/journals/${journalId}`)
      .then((res) => {
        setJournal(res)
        setFormData({
          entry_date: res.entry_date.split("T")[0],
          description: res.description || "",
          lines: res.lines.map((l: any) => ({
            account_id: l.account_id,
            description: l.description || "",
            debit: l.debit,
            credit: l.credit,
          })),
        })
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [isAuthenticated, journalId])

  const addLine = () => {
    setFormData({
      ...formData,
      lines: [...formData.lines, { account_id: "", description: "", debit: "0", credit: "0" }],
    })
  }

  const removeLine = (idx: number) => {
    if (formData.lines.length <= 1) return
    const newLines = [...formData.lines]
    newLines.splice(idx, 1)
    setFormData({ ...formData, lines: newLines })
  }

  const handleLineChange = (idx: number, field: string, value: string) => {
    const newLines = [...formData.lines]
    newLines[idx] = { ...newLines[idx], [field]: value }
    setFormData({ ...formData, lines: newLines })
  }

  const getAccountLabel = (accountId: string) => {
    const acct = accounts.find((a) => a.id === accountId)
    return acct ? `${acct.code} - ${acct.name}` : ""
  }

  const totalDebit = formData.lines.reduce((sum, l) => sum + (parseFloat(l.debit) || 0), 0)
  const totalCredit = formData.lines.reduce((sum, l) => sum + (parseFloat(l.credit) || 0), 0)
  const isBalanced = Math.abs(totalDebit - totalCredit) < 0.01

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!isBalanced) {
      setError("Journal entry must be balanced (debits = credits)")
      return
    }
    setSaving(true)
    setError(null)
    try {
      const payload = {
        entry_date: formData.entry_date,
        description: formData.description,
        lines: formData.lines.map((l) => ({
          account_id: l.account_id,
          description: l.description || undefined,
          debit: parseFloat(l.debit) || 0,
          credit: parseFloat(l.credit) || 0,
        })),
      }
      if (isEdit) {
        await api.patch(`/journals/${journalId}`, payload)
      } else {
        await api.post("/journals", payload)
      }
      router.push("/accounting/journals")
    } catch (err: any) {
      setError(err.detail || "Failed to save journal entry")
    } finally {
      setSaving(false)
    }
  }

  const handlePost = async () => {
    if (!journalId || journal?.status !== "draft") return
    setSaving(true)
    try {
      await api.post(`/journals/${journalId}/post`, {})
      router.push(`/accounting/journals/${journalId}`)
    } catch (err: any) {
      setError(err.detail || "Failed to post journal entry")
    } finally {
      setSaving(false)
    }
  }

  const handleVoid = async () => {
    if (!journalId || journal?.status !== "posted") return
    if (!confirm("Void this journal entry? This cannot be undone.")) return
    setSaving(true)
    try {
      await api.post(`/journals/${journalId}/void`, {})
      router.push(`/accounting/journals/${journalId}`)
    } catch (err: any) {
      setError(err.detail || "Failed to void journal entry")
    } finally {
      setSaving(false)
    }
  }

  const handleReverse = async () => {
    if (!journalId || journal?.status !== "posted") return
    setSaving(true)
    try {
      await api.post(`/journals/${journalId}/reverse`, {})
      router.push("/accounting/journals")
    } catch (err: any) {
      setError(err.detail || "Failed to reverse journal entry")
    } finally {
      setSaving(false)
    }
  }

  if (authLoading || loading) return <div className="p-6">Loading...</div>
  if (!isAuthenticated) return null

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">
          {isEdit ? `Edit Journal ${journal?.number || ""}` : "New Journal Entry"}
        </h1>
        {journal && (
          <StatusBadge
            status={journal.status === "posted" ? "posted" : journal.status === "void" ? "void" : "draft"}
          >
            {journal.status.toUpperCase()}
          </StatusBadge>
        )}
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium">Entry Date *</label>
            <input
              type="date"
              value={formData.entry_date}
              onChange={(e) => setFormData({ ...formData, entry_date: e.target.value })}
              className="mt-1 block w-full rounded-md border border-input px-3 py-2 bg-background"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium">Description</label>
            <input
              type="text"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="mt-1 block w-full rounded-md border border-input px-3 py-2 bg-background"
            />
          </div>
        </div>

        <div className="border rounded-lg overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="bg-muted">
                <th className="text-left p-2 text-sm">Account</th>
                <th className="text-left p-2 text-sm">Description</th>
                <th className="text-right p-2 text-sm">Debit</th>
                <th className="text-right p-2 text-sm">Credit</th>
                <th className="w-10 p-2"></th>
              </tr>
            </thead>
            <tbody>
              {formData.lines.length === 0 && (
                <tr>
                  <td colSpan={5} className="p-4 text-center text-muted-foreground">
                    No lines yet. Add your first line below.
                  </td>
                </tr>
              )}
              {formData.lines.map((line, idx) => (
                <tr key={idx} className="border-t">
                  <td className="p-2">
                    <select
                      value={line.account_id}
                      onChange={(e) => handleLineChange(idx, "account_id", e.target.value)}
                      className="w-full rounded-md border border-input px-2 py-1 bg-background text-sm"
                      required
                    >
                      <option value="">Select account</option>
                      {accounts.map((a) => (
                        <option key={a.id} value={a.id}>{a.code} - {a.name} ({a.type})</option>
                      ))}
                    </select>
                  </td>
                  <td className="p-2">
                    <input
                      type="text"
                      value={line.description}
                      onChange={(e) => handleLineChange(idx, "description", e.target.value)}
                      className="w-full rounded-md border border-input px-2 py-1 bg-background text-sm"
                    />
                  </td>
                  <td className="p-2">
                    <input
                      type="number"
                      step="0.01"
                      value={line.debit}
                      onChange={(e) => handleLineChange(idx, "debit", e.target.value)}
                      className="w-full rounded-md border border-input px-2 py-1 bg-background text-sm text-right"
                    />
                  </td>
                  <td className="p-2">
                    <input
                      type="number"
                      step="0.01"
                      value={line.credit}
                      onChange={(e) => handleLineChange(idx, "credit", e.target.value)}
                      className="w-full rounded-md border border-input px-2 py-1 bg-background text-sm text-right"
                    />
                  </td>
                  <td className="p-2 text-center">
                    <button
                      type="button"
                      onClick={() => removeLine(idx)}
                      className="text-destructive hover:text-destructive/80"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="bg-muted border-t-2">
                <td colSpan={2} className="p-2 text-right font-medium">Totals:</td>
                <td className="p-2 text-right font-mono font-bold">{totalDebit.toFixed(2)}</td>
                <td className="p-2 text-right font-mono font-bold">{totalCredit.toFixed(2)}</td>
                <td></td>
              </tr>
            </tfoot>
          </table>
        </div>

        <div className="flex justify-between items-center">
          <button
            type="button"
            onClick={addLine}
            className="border border-input px-3 py-1 rounded text-sm flex items-center gap-2"
          >
            <Plus className="h-4 w-4" /> Add Line
          </button>
          {!isBalanced && formData.lines.length > 0 && (
            <div className="text-sm text-destructive">
              Unbalanced: {formatCurrency(totalDebit.toFixed(2))} debit / {formatCurrency(totalCredit.toFixed(2))} credit
            </div>
          )}
        </div>

        <div className="flex gap-2">
          <button
            type="submit"
            disabled={saving || !isBalanced}
            className="bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm disabled:opacity-50"
          >
            {saving ? "Saving..." : isEdit ? "Update" : "Create Journal Entry"}
          </button>
          {isEdit && journal?.status === "draft" && (
            <button
              type="button"
              onClick={handlePost}
              disabled={saving}
              className="border border-input px-4 py-2 rounded text-sm disabled:opacity-50"
            >
              {saving ? "Posting..." : "Post"}
            </button>
          )}
          {isEdit && journal?.status === "posted" && (
            <>
              <button
                type="button"
                onClick={handleReverse}
                disabled={saving}
                className="border border-input px-4 py-2 rounded text-sm disabled:opacity-50"
              >
                Reverse
              </button>
              <button
                type="button"
                onClick={handleVoid}
                disabled={saving}
                className="border border-destructive text-destructive px-4 py-2 rounded text-sm disabled:opacity-50"
              >
                Void
              </button>
            </>
          )}
          <button
            type="button"
            onClick={() => router.push("/accounting/journals")}
            className="border border-input px-4 py-2 rounded text-sm"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  )
}

function formatCurrency(value: string): string {
  const num = parseFloat(value)
  if (isNaN(num)) return "-"
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(num)
}
