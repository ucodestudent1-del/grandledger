"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { useAuth, formatCurrency } from "@/app/hooks/useAuth"
import { Bill } from "@/types/api"
import { Plus } from "lucide-react"

export default function BillsPage() {
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [bills, setBills] = useState<Bill[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!isAuthenticated) return
    api.get<Bill[]>("/bills?page=1&page_size=20")
      .then(setBills)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [isAuthenticated])

  if (authLoading) return <div className="p-6">Loading...</div>
  if (!isAuthenticated) return null
  if (loading) return <div className="p-6">Loading bills...</div>

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Bills</h1>
        <button
          className="bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm flex items-center gap-2"
           onClick={() => (window.location.href = "/bills/new")}
        >
          <Plus className="h-4 w-4" />
          New Bill
        </button>
      </div>

      <div className="border rounded-lg overflow-hidden">
        <table className="w-full">
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
                <td className="p-3">{formatCurrency(b.total)}</td>
                <td className="p-3 capitalize">{b.status}</td>
                <td className="p-3 text-right">
                  <button
                    className="text-sm text-primary hover:underline"
                     onClick={() => (window.location.href = `/bills/${b.id}`)}
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


