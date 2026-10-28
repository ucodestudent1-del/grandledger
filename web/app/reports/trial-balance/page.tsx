"use client"

import { useState } from "react"
import { api } from "@/lib/api"
import { useAuth, formatCurrency } from "@/app/hooks/useAuth"
import { format, startOfYear, endOfYear } from "date-fns"
import { Loader2 } from "lucide-react"

interface TBAccount {
  account_id: string
  account_code: string
  account_name: string
  account_type: string
  debit: string
  credit: string
}

interface TrialBalanceReport {
  report: string
  period: { start_date: string; end_date: string }
  accounts: TBAccount[]
  total_debits: string
  total_credits: string
}

export default function TrialBalancePage() {
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [startDate, setStartDate] = useState(format(startOfYear(new Date()), "yyyy-MM-dd"))
  const [endDate, setEndDate] = useState(format(endOfYear(new Date()), "yyyy-MM-dd"))
  const [report, setReport] = useState<TrialBalanceReport | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const res = await api.post<TrialBalanceReport>("/reports/trial-balance", {
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

  const totalDebits = parseFloat(report?.total_debits || "0")
  const totalCredits = parseFloat(report?.total_credits || "0")
  const isBalanced = totalDebits === totalCredits

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Trial Balance</h1>

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
          <div className="border rounded-lg overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="bg-muted">
                  <th className="text-left p-3 font-mono">Code</th>
                  <th className="text-left p-3">Account</th>
                  <th className="text-left p-3">Type</th>
                  <th className="text-right p-3">Debit</th>
                  <th className="text-right p-3">Credit</th>
                </tr>
              </thead>
              <tbody>
                {report.accounts.map((acct) => (
                  <tr key={acct.account_id} className="border-t">
                    <td className="p-3 font-mono text-sm">{acct.account_code}</td>
                    <td className="p-3">{acct.account_name}</td>
                    <td className="p-3 capitalize">{acct.account_type}</td>
                    <td className="p-3 text-right font-mono">{formatCurrency(acct.debit)}</td>
                    <td className="p-3 text-right font-mono">{formatCurrency(acct.credit)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex justify-between items-center border-t pt-4">
            <div>
              <span className="font-medium">Total Debits:</span>{" "}
              <span className="font-bold">{formatCurrency(totalDebits.toString())}</span>
            </div>
            <div>
              <span className="font-medium">Total Credits:</span>{" "}
              <span className="font-bold">{formatCurrency(totalCredits.toString())}</span>
            </div>
            <div className={isBalanced ? "text-green-600" : "text-red-600 font-bold"}>
              {isBalanced ? "Balanced" : "NOT BALANCED"}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
