"use client"

import { useState } from "react"
import { api } from "@/lib/api"
import { formatCurrency, useAuth } from "@/app/hooks/useAuth"
import { format, startOfYear, endOfYear } from "date-fns"
import { Loader2 } from "lucide-react"

interface PnLAccount {
  account: string
  amount: string
  type: string
}

interface PnLReport {
  report: string
  period: { start_date: string; end_date: string }
  revenue: PnLAccount[]
  expenses: PnLAccount[]
  net_income: string
}

export default function ProfitLossPage() {
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [startDate, setStartDate] = useState(format(startOfYear(new Date()), "yyyy-MM-dd"))
  const [endDate, setEndDate] = useState(format(endOfYear(new Date()), "yyyy-MM-dd"))
  const [report, setReport] = useState<PnLReport | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const res = await api.post<PnLReport>("/reports/profit-loss", {
        start_date: startDate,
        end_date: endDate,
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

  const revenueTotal = (report?.revenue || []).reduce(
    (sum, r) => sum + parseFloat(r.amount || "0"),
    0
  )
  const expenseTotal = (report?.expenses || []).reduce(
    (sum, e) => sum + parseFloat(e.amount || "0"),
    0
  )

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Profit & Loss</h1>

      <form onSubmit={handleSubmit} className="flex flex-wrap gap-4 items-end">
        <div>
          <label className="block text-sm font-medium">Start Date</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="mt-1 rounded-md border border-input px-3 py-2 bg-background"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium">End Date</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
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
        <div className="border rounded-lg p-6 space-y-4">
          <h2 className="text-xl font-semibold">{report.report}</h2>
          <p className="text-sm text-muted-foreground">
            Period: {report.period.start_date} to {report.period.end_date}
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="border rounded-lg p-4">
              <h3 className="font-medium text-muted-foreground">Revenue</h3>
              {report.revenue && report.revenue.length > 0 ? (
                <div className="space-y-1 mt-2">
                  {report.revenue.map((r, i) => (
                    <div key={i} className="flex justify-between">
                      <span className="text-sm">{r.account}</span>
                      <span className="font-medium">{formatCurrency(r.amount)}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground mt-2">No revenue accounts</p>
              )}
              <p className="text-2xl font-bold mt-2">{formatCurrency(revenueTotal.toString())}</p>
            </div>

            <div className="border rounded-lg p-4">
              <h3 className="font-medium text-muted-foreground">Expenses</h3>
              {report.expenses && report.expenses.length > 0 ? (
                <div className="space-y-1 mt-2">
                  {report.expenses.map((e, i) => (
                    <div key={i} className="flex justify-between">
                      <span className="text-sm">{e.account}</span>
                      <span className="font-medium">{formatCurrency(e.amount)}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground mt-2">No expense accounts</p>
              )}
              <p className="text-2xl font-bold mt-2">{formatCurrency(expenseTotal.toString())}</p>
            </div>
          </div>

          <div className="border-t pt-4 mt-4">
            <div className="flex justify-between items-center">
              <h3 className="font-medium">Net Income</h3>
              <p className="text-2xl font-bold text-green-600">
                {formatCurrency(report.net_income || "0")}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
