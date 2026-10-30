"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { api } from "@/lib/api"
import { useAuth, formatCurrency } from "@/app/hooks/useAuth"
import { Contact, Invoice, Bill, Payment } from "@/types/api"
import { Save, Plus, Trash2, Loader2 } from "lucide-react"

interface PaymentAllocation {
  invoice_id: string
  amount: string
}

export default function PaymentsPage() {
  const { isAuthenticated, loading: authLoading } = useAuth()
  const router = useRouter()
  const [payments, setPayments] = useState<Payment[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [contacts, setContacts] = useState<Contact[]>([])
  const [selectedContact, setSelectedContact] = useState<Contact | null>(null)
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [formData, setFormData] = useState({
    type: "receipt" as "receipt" | "payment",
    contact_id: "",
    amount: "0.00",
    payment_date: new Date().toISOString().split("T")[0],
    reference: "",
    allocations: [] as PaymentAllocation[],
  })

  useEffect(() => {
    if (!isAuthenticated) return
    api.get<Payment[]>("/payments?page=1&page_size=50")
      .then(setPayments)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [isAuthenticated])

  const loadContacts = async (type: "customer" | "vendor") => {
    const res = await api.get<Contact[]>((`/contacts?type=${type}`))
    setContacts(res)
  }

  const handleTypeChange = (type: "receipt" | "payment") => {
    setFormData({ ...formData, type, contact_id: "", allocations: [] })
    setInvoices([])
    setSelectedContact(null)
    loadContacts(type === "receipt" ? "customer" : "vendor")
  }

  const handleContactChange = async (contactId: string) => {
    setFormData({ ...formData, contact_id: contactId })
    const contact = contacts.find((c) => c.id === contactId)
    setSelectedContact(contact || null)

    if (formData.type === "receipt") {
      const res = await api.get<Invoice[]>("/invoices?status=issued")
      const contactInvoices = res.filter((inv) => inv.contact_id === contactId)
      setInvoices(contactInvoices)
    } else {
      const res = await api.get<Bill[]>("/bills?status_filter=posted")
      const contactBills = res.filter((b) => b.contact_id === contactId)
      setInvoices(contactBills as any)
    }
  }

  const addAllocation = () => {
    setFormData({
      ...formData,
      allocations: [...formData.allocations, { invoice_id: "", amount: "0.00" }],
    })
  }

  const removeAllocation = (idx: number) => {
    const newAllocations = [...formData.allocations]
    newAllocations.splice(idx, 1)
    setFormData({ ...formData, allocations: newAllocations })
  }

  const updateAllocation = (idx: number, field: string, value: string) => {
    const newAllocations = [...formData.allocations]
    newAllocations[idx] = { ...newAllocations[idx], [field]: value }
    setFormData({ ...formData, allocations: newAllocations })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      await api.post("/payments", {
        type: formData.type,
        contact_id: formData.contact_id,
        amount: parseFloat(formData.amount) || 0,
        payment_date: formData.payment_date,
        reference: formData.reference || undefined,
        allocated_to: formData.allocations.length > 0 ? formData.allocations : undefined,
      })
      setShowForm(false)
      setPayments([...payments, {
        id: "",
        company_id: "",
        contact_id: formData.contact_id,
        type: formData.type,
        amount: formData.amount,
        payment_date: formData.payment_date,
        created_at: new Date().toISOString(),
      } as Payment])
    } catch (err: any) {
      setError(err.detail || "Failed to save payment")
    } finally {
      setSaving(false)
    }
  }

  const totalAllocated = formData.allocations.reduce(
    (sum, a) => sum + (parseFloat(a.amount) || 0),
    0
  )

  if (authLoading) return <div className="p-6">Loading...</div>
  if (!isAuthenticated) return null

  if (loading) return <div className="p-6">Loading payments...</div>

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Payments</h1>
        <button
          onClick={() => setShowForm(true)}
          className="bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm flex items-center gap-2"
        >
          <Plus className="h-4 w-4" /> New Payment
        </button>
      </div>

      {showForm && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-card border rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">
              {formData.type === "receipt" ? "Record Receipt" : "Record Payment"}
            </h2>
            {error && <p className="text-sm text-destructive mb-4">{error}</p>}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="flex gap-4">
                <label className="flex items-center gap-2">
                  <input
                    type="radio"
                    name="type"
                    checked={formData.type === "receipt"}
                    onChange={() => handleTypeChange("receipt")}
                  />
                  Receipt (Customer pays us)
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="radio"
                    name="type"
                    value="payment"
                    checked={formData.type === "payment"}
                    onChange={() => handleTypeChange("payment")}
                  />
                  Payment (We pay vendor)
                </label>
              </div>

              <div>
                <label className="block text-sm font-medium">{formData.type === "receipt" ? "Customer" : "Vendor"} *</label>
                <select
                  value={formData.contact_id}
                  onChange={(e) => handleContactChange(e.target.value)}
                  className="mt-1 block w-full rounded-md border border-input px-3 py-2 bg-background"
                  required
                >
                  <option value="">Select {formData.type === "receipt" ? "customer" : "vendor"}</option>
                  {contacts.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>

              {selectedContact && (
                <div className="text-sm text-muted-foreground">
                  {selectedContact.email && <span>Email: {selectedContact.email}</span>}
                  {selectedContact.phone && <span className="ml-2">Phone: {selectedContact.phone}</span>}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium">Amount *</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.amount}
                  onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                  className="mt-1 block w-full rounded-md border border-input px-3 py-2 bg-background"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium">Payment Date</label>
                <input
                  type="date"
                  value={formData.payment_date}
                  onChange={(e) => setFormData({ ...formData, payment_date: e.target.value })}
                  className="mt-1 block w-full rounded-md border border-input px-3 py-2 bg-background"
                />
              </div>

              <div>
                <label className="block text-sm font-medium">Reference</label>
                <input
                  type="text"
                  value={formData.reference}
                  onChange={(e) => setFormData({ ...formData, reference: e.target.value })}
                  className="mt-1 block w-full rounded-md border border-input px-3 py-2 bg-background"
                  placeholder="Check number, transaction ID, etc."
                />
              </div>

              {invoices.length > 0 && (
                <div className="space-y-2">
                  <label className="block text-sm font-medium">Allocate to Invoices/Bills</label>
                  {formData.allocations.map((alloc, idx) => (
                    <div key={idx} className="flex gap-2 items-center">
                      <select
                        value={alloc.invoice_id}
                        onChange={(e) => updateAllocation(idx, "invoice_id", e.target.value)}
                        className="flex-1 rounded-md border border-input px-2 py-1 bg-background text-sm"
                      >
                        <option value="">Select {formData.type === "receipt" ? "invoice" : "bill"}</option>
                        {invoices.map((inv) => (
                          <option key={inv.id} value={inv.id}>
                            {inv.number} — {formatCurrency(inv.total)} (Due: {inv.due_date || "—"})
                          </option>
                        ))}
                      </select>
                      <input
                        type="number"
                        step="0.01"
                        value={alloc.amount}
                        onChange={(e) => updateAllocation(idx, "amount", e.target.value)}
                        className="w-24 rounded-md border border-input px-2 py-1 bg-background text-sm text-right"
                      />
                      <button
                        type="button"
                        onClick={() => removeAllocation(idx)}
                        className="text-destructive hover:text-destructive/80"
                      >
                        <Trash2 className="h-3 w-3" />
                      </button>
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={addAllocation}
                    className="text-sm text-primary hover:underline flex items-center gap-1"
                  >
                    <Plus className="h-3 w-3" /> Add allocation
                  </button>
                  <div className="text-sm">
                    Total allocated: <strong>{formatCurrency(totalAllocated.toString())}</strong>
                    {" "}vs Amount: <strong>{formatCurrency(formData.amount)}</strong>
                  </div>
                </div>
              )}

              <div className="flex gap-2 pt-4 border-t">
                <button
                  type="submit"
                  disabled={saving}
                  className="bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm disabled:opacity-50"
                >
                  {saving ? "Saving..." : "Save Payment"}
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
              <th className="text-left p-3">Type</th>
              <th className="text-left p-3">Contact</th>
              <th className="text-right p-3">Amount</th>
              <th className="text-left p-3">Date</th>
              <th className="text-left p-3">Reference</th>
            </tr>
          </thead>
          <tbody>
            {payments.length === 0 ? (
              <tr>
                <td colSpan={5} className="p-4 text-center text-muted-foreground">
                  No payments recorded.
                </td>
              </tr>
            ) : (
              payments.map((p) => (
                <tr key={p.id} className="border-t">
                  <td className="p-3 capitalize">{p.type}</td>
                  <td className="p-3">{selectedContact?.name || p.contact_id}</td>
                  <td className="p-3 text-right">{formatCurrency(p.amount.toString())}</td>
                  <td className="p-3 text-sm">{p.payment_date}</td>
                  <td className="p-3 text-sm">{p.reference || "-"}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
