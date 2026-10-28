"use client"

import { useState } from "react"
import { api } from "@/lib/api"
import { useAuth, formatCurrency } from "@/app/hooks/useAuth"
import { format, startOfYear, endOfYear } from "date-fns"
import { Loader2 } from "lucide-react"

interface GLEntry {
  date: string
  description: string
  debit: string
  credit: string
  reference: string
}

interface GLAccount {
  account_id: string
  account_code: string
  account_name: string
  entries: GLEntry[]
  debit_total: string
  credit_total: string
}

interface GLReport {
  report: string
  period: { start_date: string; end_date: string }
  accounts: GLAccount[]
}

export default function GeneralLedgerPage() {
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [startDate, setStartDate] = useState(format(startOfYear(new Date()), "yyyy-MM-dd"))
  const [endDate, setEndDate] = useState(format(endOfYear(new Date()), "yyyy-MM-dd"))
  const [report, setReport] = useState<GLReport | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const res = await api.post<GLReport>("/reports/general-ledger", {
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

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">General Ledger</h1>

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

      {report && report.accounts.length > 0 && (
        <div className="space-y-4">
          {report.accounts.map((acct) => (
            <div key={acct.account_id} className="border rounded-lg p-4">
              <div className="flex justify-between items-center mb-2">
                <h3 className="font-medium">
                  {acct.account_code} — {acct.account_name}
                </h3>
                <div className="text-sm text-muted-foreground">
                  Dr: {formatCurrency(acct.debit_total)} | Cr: {formatCurrency(acct.credit_total)}
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-muted">
                      <th className="text-left p-2">Date</th>
                      <th className="text-left p-2">Reference</th>
                      <th className="text-left p-2">Description</th>
                      <th className="text-right p-2">Debit</th>
                      <th className="text-right p-2">Credit</th>
                    </tr>
                  </thead>
                  <tbody>
                    {acct.entries.map((entry, i) => (
                      <tr key={i} className="border-t">
                        <td className="p-2">{entry.date}</td>
                        <td className="p-2 font-mono">{entry.reference}</td>
                        <td className="p-2">{entry.description || "-"}</td>
                        <td className="p-2 text-right font-mono">{formatCurrency(entry.debit)}</td>
                        <td className="p-2 text-right font-mono">{formatCurrency(entry.credit)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
