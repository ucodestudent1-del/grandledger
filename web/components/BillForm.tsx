"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { api } from "@/lib/api"
import { useAuth } from "@/app/hooks/useAuth"
import { Bill, Contact } from "@/types/api"
import { Plus, Trash2 } from "lucide-react"

interface Account {
  id: string
  name: string
  code: string
  type: string
}

export default function BillForm({ billId }: { billId?: string }) {
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [bill, setBill] = useState<Bill | null>(null)
  const [contacts, setContacts] = useState<Contact[]>([])
  const [accounts, setAccounts] = useState<Account[]>([])
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const router = useRouter()

  const isEdit = !!billId

  const [formData, setFormData] = useState({
    contact_id: "",
    issue_date: new Date().toISOString().split("T")[0],
    due_date: "",
    lines: [{ description: "", qty: "1", unit_price: "0.00", tax_rate: "0", account_id: "" }],
  })

  useEffect(() => {
    if (!isAuthenticated) return
    const fetchData = async () => {
      try {
        const [contactsRes, accountsRes] = await Promise.all([
          api.get<Contact[]>("/contacts?type=vendor"),
          api.get<Account[]>("/accounts"),
        ])
        setContacts(contactsRes)
        setAccounts(accountsRes)
      } catch (err) {
        console.error("Failed to fetch:", err)
      }
    }
    fetchData()
    if (billId) {
      api.get<Bill>(`/bills/${billId}`)
        .then((res) => {
          setBill(res)
          setFormData({
            contact_id: res.contact_id,
            issue_date: res.issue_date || "",
            due_date: res.due_date || "",
            lines: res.lines.map((l) => ({
              description: l.description,
              qty: l.qty,
              unit_price: l.unit_price,
              tax_rate: l.tax_rate,
              account_id: l.account_id || "",
            })),
          })
        })
        .catch(console.error)
    }
  }, [isAuthenticated, billId])

  const handleLineChange = (idx: number, field: string, value: string) => {
    const newLines = [...formData.lines]
    newLines[idx] = { ...newLines[idx], [field]: value }
    setFormData({ ...formData, lines: newLines })
  }

  const addLine = () => {
    setFormData({
      ...formData,
      lines: [...formData.lines, { description: "", qty: "1", unit_price: "0.00", tax_rate: "0", account_id: "" }],
    })
  }

  const removeLine = (idx: number) => {
    if (formData.lines.length <= 1) return
    const newLines = [...formData.lines]
    newLines.splice(idx, 1)
    setFormData({ ...formData, lines: newLines })
  }

  const calculateTotals = () => {
    const subtotal = formData.lines.reduce((sum, line) => {
      const qty = parseFloat(line.qty) || 0
      const price = parseFloat(line.unit_price) || 0
      return sum + (qty * price)
    }, 0)
    const tax = formData.lines.reduce((sum, line) => {
      const qty = parseFloat(line.qty) || 0
      const price = parseFloat(line.unit_price) || 0
      const taxRate = parseFloat(line.tax_rate) || 0
      return sum + (qty * price * taxRate / 100)
    }, 0)
    return { subtotal, tax, total: subtotal + tax }
  }

  const { subtotal, tax, total } = calculateTotals()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      const payload = {
        contact_id: formData.contact_id,
        issue_date: formData.issue_date,
        due_date: formData.due_date,
        lines: formData.lines.map((l) => ({
          description: l.description,
          qty: parseFloat(l.qty) || 1,
          unit_price: parseFloat(l.unit_price) || 0,
          tax_rate: parseFloat(l.tax_rate) || 0,
          account_id: l.account_id || undefined,
        })),
      }
      if (isEdit) {
        await api.patch(`/bills/${billId}`, payload)
      } else {
        await api.post("/bills", payload)
      }
      router.push("/bills")
    } catch (err: any) {
      setError(err.detail || "Failed to save bill")
    } finally {
      setSaving(false)
    }
  }

  const handlePost = async () => {
    if (!billId || bill?.status !== "draft") return
    setSaving(true)
    try {
      await api.post(`/bills/${billId}/post`, {})
      router.push(`/bills/${billId}`)
    } catch (err: any) {
      setError(err.detail || "Failed to post bill")
    } finally {
      setSaving(false)
    }
  }

  const handleVoid = async () => {
    if (!billId || bill?.status !== "posted") return
    if (!confirm("Void this bill? This cannot be undone.")) return
    setSaving(true)
    try {
      await api.post(`/bills/${billId}/void`, {})
      router.push(`/bills/${billId}`)
    } catch (err: any) {
      setError(err.detail || "Failed to void bill")
    } finally {
      setSaving(false)
    }
  }

  if (authLoading) return <div className="p-6">Loading...</div>
  if (!isAuthenticated) return null

  const expenseAccounts = accounts.filter((a) => a.type === "expense")

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">{isEdit ? `Edit Bill ${bill?.number || ""}` : "New Bill"}</h1>
        {bill && (
          <span className={`px-2 py-1 rounded text-xs capitalize ${
            bill.status === "posted" ? "bg-green-100 text-green-800" :
            bill.status === "void" ? "bg-red-100 text-red-800" :
            "bg-yellow-100 text-yellow-800"
          }`}>
            {bill.status}
          </span>
        )}
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium">Vendor</label>
            <select
              value={formData.contact_id}
              onChange={(e) => setFormData({ ...formData, contact_id: e.target.value })}
              className="mt-1 block w-full rounded-md border border-input px-3 py-2 bg-background"
              required
            >
              <option value="">Select vendor</option>
              {contacts.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium">Issue Date</label>
            <input
              type="date"
              value={formData.issue_date}
              onChange={(e) => setFormData({ ...formData, issue_date: e.target.value })}
              className="mt-1 block w-full rounded-md border border-input px-3 py-2 bg-background"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium">Due Date</label>
            <input
              type="date"
              value={formData.due_date}
              onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
              className="mt-1 block w-full rounded-md border border-input px-3 py-2 bg-background"
            />
          </div>
        </div>

        <div className="border rounded-lg overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="bg-muted">
                <th className="text-left p-2 text-sm">Description</th>
                <th className="text-right p-2 text-sm">Qty</th>
                <th className="text-right p-2 text-sm">Unit Price</th>
                <th className="text-right p-2 text-sm">Tax %</th>
                <th className="w-10 p-2"></th>
              </tr>
            </thead>
            <tbody>
              {formData.lines.map((line, idx) => (
                <tr key={idx} className="border-t">
                  <td className="p-2">
                    <input
                      type="text"
                      value={line.description}
                      onChange={(e) => handleLineChange(idx, "description", e.target.value)}
                      className="w-full rounded-md border border-input px-2 py-1 bg-background text-sm"
                      required
                    />
                  </td>
                  <td className="p-2">
                    <input
                      type="number"
                      step="0.01"
                      value={line.qty}
                      onChange={(e) => handleLineChange(idx, "qty", e.target.value)}
                      className="w-full rounded-md border border-input px-2 py-1 bg-background text-sm text-right"
                      required
                    />
                  </td>
                  <td className="p-2">
                    <input
                      type="number"
                      step="0.01"
                      value={line.unit_price}
                      onChange={(e) => handleLineChange(idx, "unit_price", e.target.value)}
                      className="w-full rounded-md border border-input px-2 py-1 bg-background text-sm text-right"
                      required
                    />
                  </td>
                  <td className="p-2">
                    <input
                      type="number"
                      step="0.01"
                      value={line.tax_rate}
                      onChange={(e) => handleLineChange(idx, "tax_rate", e.target.value)}
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
          </table>
        </div>

        <button
          type="button"
          onClick={addLine}
          className="border border-input px-3 py-1 rounded text-sm flex items-center gap-2"
        >
          <Plus className="h-4 w-4" /> Add Line
        </button>

        <div className="flex justify-end">
          <div className="w-64 space-y-2">
            <div className="flex justify-between">
              <span>Subtotal:</span>
              <span className="font-mono">{subtotal.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span>Tax:</span>
              <span className="font-mono">{tax.toFixed(2)}</span>
            </div>
            <div className="flex justify-between font-bold border-t pt-2">
              <span>Total:</span>
              <span className="font-mono">{total.toFixed(2)}</span>
            </div>
          </div>
        </div>

        <div className="flex gap-2">
          <button
            type="submit"
            disabled={saving}
            className="bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm disabled:opacity-50"
          >
            {saving ? "Saving..." : isEdit ? "Update Bill" : "Create Bill"}
          </button>
          {isEdit && bill?.status === "draft" && (
            <button
              type="button"
              onClick={handlePost}
              disabled={saving}
              className="border border-input px-4 py-2 rounded text-sm disabled:opacity-50"
            >
              {saving ? "Posting..." : "Post Bill"}
            </button>
          )}
          {isEdit && bill?.status === "posted" && (
            <button
              type="button"
              onClick={handleVoid}
              disabled={saving}
              className="border border-destructive text-destructive px-4 py-2 rounded text-sm disabled:opacity-50"
            >
              {saving ? "Voiding..." : "Void Bill"}
            </button>
          )}
          <button
            type="button"
            onClick={() => router.push("/bills")}
            className="border border-input px-4 py-2 rounded text-sm"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  )
}
