"use client"

import Link from "next/link"
import { api } from "@/lib/api"
import { useEffect, useState } from "react"
import { Company, JournalEntry, Invoice } from "@/types/api"

export default function DashboardPage() {
  const [company, setCompany] = useState<Company | null>(null)
  const [recentEntries, setRecentEntries] = useState<JournalEntry[]>([])
  const [recentInvoices, setRecentInvoices] = useState<Invoice[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem("access_token")
    if (!token) {
      window.location.href = "/login"
      return
    }
    api.setToken(token)

    const fetchData = async () => {
      try {
        const [entries, invoices] = await Promise.all([
          api.get<JournalEntry[]>("/journals?limit=5"),
          api.get<Invoice[]>("/invoices?limit=5"),
        ])
        setRecentEntries(entries)
        setRecentInvoices(invoices)
      } catch (err) {
        console.error("Error fetching data:", err)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  if (loading) {
    return <div className="text-center py-12">Loading dashboard...</div>
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground">GrandLedger Bookkeeping</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Link href="/app/accounting/journals" className="block p-4 border rounded-lg hover:bg-muted">
          <div className="text-2xl font-bold">{recentEntries.length}</div>
          <div className="text-sm text-muted-foreground">Recent Journal Entries</div>
        </Link>
        <Link href="/app/ar/invoices" className="block p-4 border rounded-lg hover:bg-muted">
          <div className="text-2xl font-bold">{recentInvoices.length}</div>
          <div className="text-sm text-muted-foreground">Recent Invoices</div>
        </Link>
        <Link href="/app/reports/profit-loss" className="block p-4 border rounded-lg hover:bg-muted">
          <div className="text-2xl font-bold">P&L</div>
          <div className="text-sm text-muted-foreground">Profit & Loss</div>
        </Link>
        <Link href="/app/reports/balance-sheet" className="block p-4 border rounded-lg hover:bg-muted">
          <div className="text-2xl font-bold">B/S</div>
          <div className="text-sm text-muted-foreground">Balance Sheet</div>
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="border rounded-lg p-4">
          <h2 className="text-lg font-semibold mb-3">Recent Journal Entries</h2>
          <div className="space-y-2">
            {recentEntries.map((entry) => (
              <div key={entry.id} className="flex justify-between items-center py-2 border-b">
                <div>
                  <span className="font-mono text-sm">{entry.number}</span>
                  <span className="ml-2 text-sm text-muted-foreground">{entry.description}</span>
                </div>
                <span className={`text-xs px-2 py-1 rounded ${
                  entry.status === "posted" ? "bg-green-100 text-green-800" :
                  entry.status === "draft" ? "bg-yellow-100 text-yellow-800" :
                  "bg-gray-100 text-gray-800"
                }`}>
                  {entry.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="border rounded-lg p-4">
          <h2 className="text-lg font-semibold mb-3">Recent Invoices</h2>
          <div className="space-y-2">
            {recentInvoices.map((inv) => (
              <div key={inv.id} className="flex justify-between items-center py-2 border-b">
                <div>
                  <span className="font-mono text-sm">{inv.number}</span>
                  <span className="ml-2 text-sm text-muted-foreground">{inv.contact_id}</span>
                </div>
                <div className="text-right">
                  <div className="font-medium">${inv.total}</div>
                  <span className={`text-xs px-2 py-1 rounded ${
                    inv.status === "paid" ? "bg-green-100 text-green-800" :
                    inv.status === "issued" ? "bg-blue-100 text-blue-800" :
                    "bg-gray-100 text-gray-800"
                  }`}>
                    {inv.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
