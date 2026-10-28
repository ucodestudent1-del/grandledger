"use client"

import { useState } from "react"
import { api } from "@/lib/api"
import { ReportResponse } from "@/types/api"
import { format } from "date-fns"

export default function APAgingPage() {
  const [asOf, setAsOf] = useState(format(new Date(), "yyyy-MM-dd"))
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
      const res = await api.post<any>("/reports/ap-aging")
      setReport(res)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

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

      {report && (
        <div className="border rounded-lg p-6">
          <h2 className="text-xl font-semibold">{report.report}</h2>
          <p className="text-2xl font-bold">Total Outstanding: ${report.total_outstanding}</p>
          <div className="grid grid-cols-5 gap-4 mt-4">
            {Object.entries(report.buckets).map(([range, amount]: [string, unknown]) => (
              <div key={range} className="text-center">
                <div className="font-medium">{range}</div>
                <div>${String(amount)}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
