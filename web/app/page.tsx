"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { useAuth, formatCurrency } from "@/app/hooks/useAuth"
import { JournalEntry, Invoice } from "@/types/api"
import { format, endOfMonth, startOfMonth } from "date-fns"
import { Loader2 } from "lucide-react"

interface PnLReport {
  report: string
  net_income: string
  revenue: { account: string; amount: string }[]
  expenses: { account: string; amount: string }[]
}

interface BalanceSheetReport {
  report: string
  assets: { total: string }
  liabilities: { total: string }
  equity: { total: string }
}

export default function DashboardPage() {
  const { isAuthenticated, loading: authLoading, logout } = useAuth()
  const [recentEntries, setRecentEntries] = useState<JournalEntry[]>([])
  const [recentInvoices, setRecentInvoices] = useState<Invoice[]>([])
  const [pnl, setPnl] = useState<PnLReport | null>(null)
  const [bs, setBs] = useState<BalanceSheetReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!isAuthenticated) return

    const now = new Date()
    const startDate = format(startOfMonth(now), "yyyy-MM-dd")
    const endDate = format(endOfMonth(now), "yyyy-MM-dd")

    const fetchData = async () => {
      try {
        const [entries, invoices, pnlRes, bsRes] = await Promise.all([
          api.get<JournalEntry[]>("/journals?page=1&page_size=5"),
          api.get<Invoice[]>("/invoices?page=1&page_size=5"),
          api.post<PnLReport>("/reports/profit-loss", {
            start_date: startDate,
            end_date: endDate,
          }),
          api.post<BalanceSheetReport>("/reports/balance-sheet", {
            start_date: "2000-01-01",
            end_date: endDate,
          }),
        ])
        setRecentEntries(entries)
        setRecentInvoices(invoices)
        setPnl(pnlRes)
        setBs(bsRes)
      } catch (err: any) {
        setError(err.detail || "Failed to load dashboard data")
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [isAuthenticated])

  if (authLoading) return <div className="p-6">Loading...</div>
  if (!isAuthenticated) return null

  const netIncome = parseFloat(pnl?.net_income || "0")
  const assets = parseFloat(bs?.assets?.total || "0")
  const liabilities = parseFloat(bs?.liabilities?.total || "0")
  const equity = parseFloat(bs?.equity?.total || "0")

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">GrandLedger Bookkeeping</p>
        </div>
        <button
          onClick={logout}
          className="text-sm text-muted-foreground hover:text-foreground"
        >
          Logout
        </button>
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Link href="/accounting/journals" className="block p-4 border rounded-lg hover:bg-muted">
          <div className="text-2xl font-bold">{recentEntries.length}</div>
          <div className="text-sm text-muted-foreground">Recent Journal Entries</div>
        </Link>
        <Link href="/invoices" className="block p-4 border rounded-lg hover:bg-muted">
          <div className="text-2xl font-bold">{recentInvoices.length}</div>
          <div className="text-sm text-muted-foreground">Recent Invoices</div>
        </Link>
        <Link href="/reports/profit-loss" className="block p-4 border rounded-lg hover:bg-muted">
          <div className="text-2xl font-bold text-green-600">{formatCurrency(netIncome.toString())}</div>
          <div className="text-sm text-muted-foreground">Net Income (MTD)</div>
        </Link>
        <Link href="/reports/balance-sheet" className="block p-4 border rounded-lg hover:bg-muted">
          <div className="text-2xl font-bold">{formatCurrency(assets.toString())}</div>
          <div className="text-sm text-muted-foreground">Total Assets</div>
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="border rounded-lg p-4">
          <h3 className="font-medium text-muted-foreground">Liabilities</h3>
          <p className="text-xl font-bold">{formatCurrency(liabilities.toString())}</p>
        </div>
        <div className="border rounded-lg p-4">
          <h3 className="font-medium text-muted-foreground">Equity</h3>
          <p className="text-xl font-bold">{formatCurrency(equity.toString())}</p>
        </div>
        <div className="border rounded-lg p-4">
          <h3 className="font-medium text-muted-foreground">Assets - Liabilities</h3>
          <p className="text-xl font-bold">{formatCurrency((assets - liabilities).toString())}</p>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin" />
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="border rounded-lg p-4">
            <h2 className="text-lg font-semibold mb-3">Recent Journal Entries</h2>
            <div className="space-y-2">
              {recentEntries.map((entry) => (
                <div key={entry.id} className="flex justify-between items-center py-2 border-b">
                  <div>
                    <span className="font-mono text-sm">{entry.number}</span>
                    <span className="ml-2 text-sm text-muted-foreground">
                      {entry.description || "-"}
                    </span>
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
                    <span className="ml-2 text-sm text-muted-foreground">
                      {new Date(inv.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="text-right">
                    <div className="font-medium">{formatCurrency(inv.total)}</div>
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
      )}
    </div>
  )
}


