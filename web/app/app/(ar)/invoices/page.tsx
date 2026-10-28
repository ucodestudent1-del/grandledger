"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { Invoice } from "@/types/api"

export default function InvoicesPage() {
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem("access_token")
    if (!token) {
      window.location.href = "/login"
      return
    }
    api.setToken(token)
    api.get<Invoice[]>("/invoices")
      .then(setInvoices)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div>Loading...</div>

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Invoices</h1>
        <button
          className="bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm"
          onClick={() => (window.location.href = "/app/(ar)/invoices/new")}
        >
          New Invoice
        </button>
      </div>
      <div className="border rounded-lg overflow-hidden">
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-muted">
              <th className="text-left p-3">Number</th>
              <th className="text-left p-3">Total</th>
              <th className="text-left p-3">Status</th>
              <th className="text-right p-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {invoices.map((inv) => (
              <tr key={inv.id} className="border-t">
                <td className="p-3 font-mono">{inv.number}</td>
                <td className="p-3">${inv.total}</td>
                <td className="p-3">{inv.status}</td>
                <td className="p-3 text-right">
                  <button
                    className="text-sm text-primary hover:underline"
                    onClick={() => (window.location.href = `/app/(ar)/invoices/${inv.id}`)}
                  >
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
