"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { useAuth, formatCurrency } from "@/app/hooks/useAuth"
import { BankAccount, BankTransaction } from "@/types/api"
import { Plus, Upload, RefreshCw, Download } from "lucide-react"

export default function BankAccountsPage() {
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [accounts, setAccounts] = useState<BankAccount[]>([])
  const [loading, setLoading] = useState(true)
  const [importing, setImporting] = useState<string | null>(null)

  useEffect(() => {
    if (!isAuthenticated) return
    api.get<BankAccount[]>("/bank/accounts")
      .then(setAccounts)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [isAuthenticated])

  const handleCsvImport = async (accountId: string, file: File) => {
    setImporting(accountId)
    try {
      const formData = new FormData()
      formData.append("file", file)
      await api.post(`/bank/transactions/import?bank_account_id=${accountId}`, formData)
      setLoading(true)
      api.get<BankAccount[]>("/bank/accounts")
        .then(setAccounts)
        .catch(console.error)
        .finally(() => setLoading(false))
    } catch (err: any) {
      console.error("Import failed:", err)
    } finally {
      setImporting(null)
    }
  }

  if (authLoading) return <div className="p-6">Loading...</div>
  if (!isAuthenticated) return null
  if (loading) return <div className="p-6">Loading bank accounts...</div>

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Bank Accounts</h1>
        <button className="bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm flex items-center gap-2">
          <Plus className="h-4 w-4" />
          Add Bank Account
        </button>
      </div>

      <div className="border rounded-lg overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-muted">
              <th className="text-left p-3">Name</th>
              <th className="text-left p-3">Bank</th>
              <th className="text-left p-3">Account #</th>
              <th className="text-right p-3">Balance</th>
              <th className="text-right p-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {accounts.map((acct) => (
              <tr key={acct.id} className="border-t">
                <td className="p-3">{acct.name}</td>
                <td className="p-3">{acct.bank_name || "-"}</td>
                <td className="p-3">{acct.account_number || "-"}</td>
                <td className="p-3 text-right">{formatCurrency(acct.starting_balance)}</td>
                <td className="p-3 text-right">
                  <label className="inline-flex items-center gap-2 border border-input px-2 py-1 rounded text-sm cursor-pointer hover:bg-accent">
                    <Upload className="h-4 w-4" />
                    {importing === acct.id ? "Importing..." : "Import CSV"}
                    <input
                      type="file"
                      accept=".csv"
                      className="hidden"
                      onChange={(e) => {
                        const file = e.target.files?.[0]
                        if (file) handleCsvImport(acct.id, file)
                        e.target.value = ""
                      }}
                    />
                  </label>
                  <button
                    onClick={() => (window.location.href = `/bank/reconcile?account=${acct.id}`)}
                    className="ml-2 text-sm text-primary hover:underline"
                  >
                    Reconcile
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="text-sm text-muted-foreground">
        <Download className="h-4 w-4 inline mr-1" />
        CSV format: date,description,amount,balance
      </div>
    </div>
  )
}


