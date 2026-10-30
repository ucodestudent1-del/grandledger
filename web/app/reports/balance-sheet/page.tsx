"use client"

import { useState } from "react"
import { api } from "@/lib/api"
import { useAuth, formatCurrency } from "@/app/hooks/useAuth"
import { format } from "date-fns"
import { Loader2 } from "lucide-react"

interface BSItem {
  account_name: string
  amount: string
}

interface BalanceSheetReport {
  report: string
  as_of: string
  assets: { total: string; items: BSItem[] }
  liabilities: { total: string; items: BSItem[] }
  equity: { total: string; items: BSItem[] }
}

export default function BalanceSheetPage() {
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [asOf, setAsOf] = useState(format(new Date(), "yyyy-MM-dd"))
  const [report, setReport] = useState<BalanceSheetReport | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const res = await api.post<BalanceSheetReport>("/reports/balance-sheet", {
        start_date: "2000-01-01",
        end_date: asOf,
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

  const assets = parseFloat(report?.assets?.total || "0")
  const liabilities = parseFloat(report?.liabilities?.total || "0")
  const equity = parseFloat(report?.equity?.total || "0")
  const calculatedEquity = assets - liabilities

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Balance Sheet</h1>

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
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="border rounded-lg p-4">
              <h3 className="font-medium text-muted-foreground">Assets</h3>
              {report.assets.items.length > 0 ? (
                <div className="space-y-1 mt-2">
                  {report.assets.items.map((item, i) => (
                    <div key={i} className="flex justify-between text-sm">
                      <span>{item.account_name}</span>
                      <span>{formatCurrency(item.amount)}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground mt-2">No asset accounts</p>
              )}
              <p className="text-2xl font-bold mt-2">{formatCurrency(assets.toString())}</p>
            </div>

            <div className="border rounded-lg p-4">
              <h3 className="font-medium text-muted-foreground">Liabilities</h3>
              {report.liabilities.items.length > 0 ? (
                <div className="space-y-1 mt-2">
                  {report.liabilities.items.map((item, i) => (
                    <div key={i} className="flex justify-between text-sm">
                      <span>{item.account_name}</span>
                      <span>{formatCurrency(item.amount)}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground mt-2">No liability accounts</p>
              )}
              <p className="text-2xl font-bold mt-2">{formatCurrency(liabilities.toString())}</p>
            </div>

            <div className="border rounded-lg p-4">
              <h3 className="font-medium text-muted-foreground">Equity</h3>
              {report.equity.items.length > 0 ? (
                <div className="space-y-1 mt-2">
                  {report.equity.items.map((item, i) => (
                    <div key={i} className="flex justify-between text-sm">
                      <span>{item.account_name}</span>
                      <span>{formatCurrency(item.amount)}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground mt-2">No equity accounts</p>
              )}
              <p className="text-2xl font-bold mt-2">{formatCurrency(equity.toString())}</p>
              <p className="text-xs text-muted-foreground">
                Calculated: {formatCurrency(calculatedEquity.toString())}
              </p>
            </div>
          </div>

          <div className="border-t pt-4">
            <div className="flex justify-between items-center">
              <span className="font-medium">Total Liabilities + Equity</span>
              <span className="font-bold">{formatCurrency((liabilities + equity).toString())}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
