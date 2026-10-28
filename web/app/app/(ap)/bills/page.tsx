"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { Bill } from "@/types/api"

export default function BillsPage() {
  const [bills, setBills] = useState<Bill[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem("access_token")
    if (!token) {
      window.location.href = "/login"
      return
    }
    api.setToken(token)
    api.get<Bill[]>("/bills")
      .then(setBills)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div>Loading...</div>

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Bills</h1>
        <button
          className="bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm"
          onClick={() => (window.location.href = "/app/(ap)/bills/new")}
        >
          New Bill
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
            {bills.map((b) => (
              <tr key={b.id} className="border-t">
                <td className="p-3 font-mono">{b.number}</td>
                <td className="p-3">${b.total}</td>
                <td className="p-3">{b.status}</td>
                <td className="p-3 text-right">
                  <button
                    className="text-sm text-primary hover:underline"
                    onClick={() => (window.location.href = `/app/(ap)/bills/${b.id}`)}
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
