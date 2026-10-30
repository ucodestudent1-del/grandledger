"use client"

import { useState } from "react"
import { api } from "@/lib/api"
import { useAuth, formatCurrency } from "@/app/hooks/useAuth"
import { format } from "date-fns"
import { Loader2 } from "lucide-react"

interface Bucket {
  [key: string]: string
}

interface AgingContact {
  contact_name: string
  total_due: string
  buckets: Bucket
}

interface AgingVendor {
  vendor_name: string
  total_due: string
  buckets: Bucket
}

interface AgingReport {
  report: string
  as_of: string
  total_outstanding: string
  buckets: Bucket
  contacts?: AgingContact[]
  vendors?: AgingVendor[]
}

export default function APAgingPage() {
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [asOf, setAsOf] = useState(format(new Date(), "yyyy-MM-dd"))
  const [report, setReport] = useState<AgingReport | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const res = await api.post<AgingReport>("/reports/ap-aging", {
        start_date: asOf,
        end_date: asOf,
        as_of: asOf,
      })
      setReport(res)
    } catch (err: any) {
      setError(err.detail || "Failed to generate report")
    } finally {
      setLoading(false)
    }
  }

  if (authLoading) return <div className="p-6">Loading...</div>
  if (!isAuthenticated) return null

  const bucketOrder = ["current", "0-30", "31-60", "61-90", "90+"]

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">AP Aging</h1>

      <form onSubmit={handleSubmit} className="flex gap-4 items-end">
        <div>
          <label className="block text-sm font-medium">As Of Date</label>
          <input
            type="date"
            value={asOf}
            onChange={(e) => setAsOf(e.target.value)}
            className="mt-1 rounded-md border border-input px-3 py-2 bg-background"
            required
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm disabled:opacity-50"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Generate"}
        </button>
      </form>

      {error && <p className="text-sm text-destructive">{error}</p>}

      {report && (
        <div className="space-y-4">
          <div className="text-2xl font-bold">
            Total Outstanding: {formatCurrency(report.total_outstanding)}
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
            {bucketOrder.map((bucket) => (
              <div key={bucket} className="border rounded-lg p-4 text-center">
                <div className="font-medium text-sm text-muted-foreground">{bucket}</div>
                <div className="text-lg font-bold">
                  {formatCurrency(report.buckets[bucket] || "0")}
                </div>
              </div>
            ))}
          </div>

          {report.vendors && report.vendors.length > 0 && (
            <div className="border rounded-lg overflow-hidden">
              <table className="w-full">
                <thead>
                  <tr className="bg-muted">
                    <th className="text-left p-3">Vendor</th>
                    {bucketOrder.map((b) => (
                      <th key={b} className="text-right p-3 text-xs">{b}</th>
                    ))}
                    <th className="text-right p-3">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {report.vendors.map((v, i) => (
                    <tr key={i} className="border-t">
                      <td className="p-3">{v.vendor_name}</td>
                      {bucketOrder.map((b) => (
                        <td key={b} className="p-3 text-right text-sm font-mono">
                          {formatCurrency(v.buckets[b] || "0")}
                        </td>
                      ))}
                      <td className="p-3 text-right font-bold">{formatCurrency(v.total_due)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
