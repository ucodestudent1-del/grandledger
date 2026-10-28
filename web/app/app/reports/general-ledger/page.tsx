"use client"

import { useState } from "react"
import { api } from "@/lib/api"
import { ReportResponse } from "@/types/api"
import { format, startOfYear, endOfYear } from "date-fns"

export default function GeneralLedgerPage() {
  const [startDate, setStartDate] = useState(format(startOfYear(new Date()), "yyyy-MM-dd"))
  const [endDate, setEndDate] = useState(format(endOfYear(new Date()), "yyyy-MM-dd"))
  const [report, setReport] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const token = localStorage.getItem("access_token")
      if (!token) {
        window.location.href = "/login"
        return
      }
      api.setToken(token)
      const res = await api.post<any>("/reports/general-ledger", {
        start_date: startDate,
        end_date: endDate,
      })
      setReport(res)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">General Ledger</h1>

      <form onSubmit={handleSubmit} className="flex gap-4 items-end">
        <div>
          <label className="block text-sm font-medium">Start Date</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="mt-1 rounded-md border border-input px-3 py-2"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium">End Date</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="mt-1 rounded-md border border-input px-3 py-2"
            required
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm"
        >
          {loading ? "Loading..." : "Generate"}
        </button>
      </form>

      {report && report.accounts && report.accounts.length > 0 && (
        <div className="space-y-4">
          {report.accounts.map((acct: any) => (
            <div key={acct.account_id} className="border rounded-lg p-4">
              <h3 className="font-medium">{acct.account_code} - {acct.account_name}</h3>
              <div className="text-sm text-muted-foreground">
                Debit: {acct.debit_total} | Credit: {acct.credit_total}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
