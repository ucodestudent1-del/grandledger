"use client"

import { useState } from "react"
import { api } from "@/lib/api"
import { useAuth, formatCurrency } from "@/app/hooks/useAuth"
import { Invoice, Contact } from "@/types/api"
import { Plus, Trash2, FileDown } from "lucide-react"
import { useRouter } from "next/navigation"

export default function InvoiceForm({ invoiceId }: { invoiceId?: string }) {
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [invoice, setInvoice] = useState<Invoice | null>(null)
  const [contacts, setContacts] = useState<Contact[]>([])
  const [accounts, setAccounts] = useState<{ id: string; name: string; code: string }[]>([])
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()

  const [formData, setFormData] = useState({
    contact_id: "",
    issue_date: new Date().toISOString().split("T")[0],
    due_date: "",
    lines: [{ description: "", qty: "1", unit_price: "0.00", tax_rate: "0", account_id: "" }],
  })

  const isEdit = !!invoiceId

  const fetchData = async () => {
    if (!isAuthenticated) return
    try {
      const [contactsRes, accountsRes] = await Promise.all([
        api.get<Contact[]>("/contacts?type=customer"),
        api.get<{ id: string; name: string; code: string }[]>("/accounts"),
      ])
      setContacts(contactsRes)
      const revenueAccounts = accountsRes.filter((a: any) => a.type === "revenue" || a.type === "expense" || a.type === "asset")
      setAccounts(accountsRes.filter((a: any) => a.type !== "revenue") as any)
    } catch (err) {
      console.error("Failed to fetch:", err)
    }
  }

  const fetchInvoice = async () => {
    if (!invoiceId || !isAuthenticated) return
    try {
      const res = await api.get<Invoice>(`/invoices/${invoiceId}`)
      setInvoice(res)
      setFormData({
        contact_id: res.contact_id,
        issue_date: res.issue_date?.split("T")[0] || "",
        due_date: res.due_date?.split("T")[0] || "",
        lines: res.lines.map((l) => ({
          description: l.description,
          qty: l.qty,
          unit_price: l.unit_price,
          tax_rate: l.tax_rate,
          account_id: l.account_id || "",
        })),
      })
    } catch (err: any) {
      setError(err.detail || "Failed to load invoice")
    }
  }

  useState(() => {
    if (isAuthenticated) {
      fetchData()
      if (invoiceId) fetchInvoice()
    }
  })

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

  const calculateLineTotal = (line: any) => {
    const qty = parseFloat(line.qty) || 0
    const price = parseFloat(line.unit_price) || 0
    const taxRate = parseFloat(line.tax_rate) || 0
    const amount = qty * price
    const tax = amount * taxRate / 100
    return amount + tax
  }

  const calculateSubtotal = () => {
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

  const { subtotal, tax, total } = calculateSubtotal()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      const lines = formData.lines.map((l) => ({
        description: l.description,
        qty: parseFloat(l.qty) || 1,
        unit_price: parseFloat(l.unit_price) || 0,
        tax_rate: parseFloat(l.tax_rate) || 0,
        account_id: l.account_id || undefined,
      }))

      if (isEdit) {
        await api.patch(`/invoices/${invoiceId}`, { contact_id: formData.contact_id, issue_date: formData.issue_date, due_date: formData.due_date, lines })
      } else {
        await api.post("/invoices", {
          contact_id: formData.contact_id,
          issue_date: formData.issue_date,
          due_date: formData.due_date,
          lines,
        })
      }
      router.push("/invoices")
    } catch (err: any) {
      setError(err.detail || "Failed to save invoice")
    } finally {
      setSaving(false)
    }
  }

  const handleIssue = async () => {
    if (!invoiceId) return
    setSaving(true)
    try {
      await api.post(`/invoices/${invoiceId}/issue`, {})
      fetchInvoice()
    } catch (err: any) {
      setError(err.detail || "Failed to issue invoice")
    } finally {
      setSaving(false)
    }
  }

  const handleVoid = async () => {
    if (!invoiceId) return
    if (!confirm("Void this invoice? This cannot be undone.")) return
    setSaving(true)
    try {
      await api.post(`/invoices/${invoiceId}/void`, {})
      fetchInvoice()
    } catch (err: any) {
      setError(err.detail || "Failed to void invoice")
    } finally {
      setSaving(false)
    }
  }

  const handleDownloadPdf = () => {
    if (!invoiceId) return
    window.open(`/api/v1/invoices/${invoiceId}/pdf`, "_blank")
  }

  if (authLoading) return <div className="p-6">Loading...</div>
  if (!isAuthenticated) return null

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">{isEdit ? `Edit Invoice ${invoice?.number || ""}` : "New Invoice"}</h1>
        {invoice && invoice.status === "issued" && (
          <button onClick={handleDownloadPdf} className="border px-3 py-1 rounded text-sm flex items-center gap-2">
            <FileDown className="h-4 w-4" /> PDF
          </button>
        )}
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium">Customer</label>
            <select
              value={formData.contact_id}
              onChange={(e) => setFormData({ ...formData, contact_id: e.target.value })}
              className="mt-1 block w-full rounded-md border border-input px-3 py-2 bg-background"
              required
            >
              <option value="">Select customer</option>
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
                <th className="text-right p-2 text-sm">Account</th>
                <th className="text-right p-2 text-sm">Amount</th>
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
                  <td className="p-2">
                    <select
                      value={line.account_id}
                      onChange={(e) => handleLineChange(idx, "account_id", e.target.value)}
                      className="w-full rounded-md border border-input px-2 py-1 bg-background text-sm"
                    >
                      <option value="">Auto-select</option>
                      {accounts.map((a) => (
                        <option key={a.id} value={a.id}>{a.code} - {a.name}</option>
                      ))}
                    </select>
                  </td>
                  <td className="p-2 text-right font-mono">
                    {formatCurrency(calculateLineTotal(line).toString())}
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
              <span className="font-mono">{formatCurrency(subtotal.toString())}</span>
            </div>
            <div className="flex justify-between">
              <span>Tax:</span>
              <span className="font-mono">{formatCurrency(tax.toString())}</span>
            </div>
            <div className="flex justify-between font-bold border-t pt-2">
              <span>Total:</span>
              <span className="font-mono">{formatCurrency(total.toString())}</span>
            </div>
          </div>
        </div>

        <div className="flex gap-2">
          <button
            type="submit"
            disabled={saving}
            className="bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm disabled:opacity-50"
          >
            {saving ? "Saving..." : isEdit ? "Update Invoice" : "Create Invoice"}
          </button>
          {isEdit && invoice && invoice.status === "draft" && (
            <button
              type="button"
              onClick={handleIssue}
              disabled={saving}
              className="border border-input px-4 py-2 rounded text-sm disabled:opacity-50"
            >
              {saving ? "Processing..." : "Issue Invoice"}
            </button>
          )}
          {isEdit && invoice && invoice.status === "issued" && (
            <button
              type="button"
              onClick={handleVoid}
              disabled={saving}
              className="border border-destructive text-destructive px-4 py-2 rounded text-sm disabled:opacity-50"
            >
              {saving ? "Processing..." : "Void Invoice"}
            </button>
          )}
          <button
            type="button"
            onClick={() => router.push("/invoices")}
            className="border border-input px-4 py-2 rounded text-sm"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  )
}
