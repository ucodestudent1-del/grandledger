"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { useAuth, formatCurrency } from "@/app/hooks/useAuth"
import { BankAccount, BankTransaction } from "@/types/api"
import { RefreshCw } from "lucide-react"

export default function ReconcilePage({ params }: { params: { id: string } }) {
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [accounts, setAccounts] = useState<BankAccount[]>([])
  const [selectedAccount, setSelectedAccount] = useState<string | null>(null)
  const [transactions, setTransactions] = useState<BankTransaction[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!isAuthenticated) return
    api.get<BankAccount[]>("/bank/accounts")
      .then(setAccounts)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [isAuthenticated])

  useEffect(() => {
    if (selectedAccount) {
      api.get<BankTransaction[]>(`/bank/transactions?bank_account_id=${selectedAccount}`)
        .then(setTransactions)
        .catch(console.error)
    }
  }, [selectedAccount])

  const handleReconcile = async (txn: BankTransaction) => {
    try {
      await api.post(`/bank/transactions/${txn.id}/reconcile`, {})
      setTransactions((prev) =>
        prev.map((t) => (t.id === txn.id ? { ...t, status: "reconciled" } : t))
      )
    } catch (err) {
      console.error("Failed to reconcile transaction:", err)
    }
  }

  if (authLoading) return <div className="p-6">Loading...</div>
  if (!isAuthenticated) return null
  if (loading) return <div className="p-6">Loading...</div>

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Bank Reconciliation</h1>

      <select
        value={selectedAccount || ""}
        onChange={(e) => setSelectedAccount(e.target.value || null)}
        className="rounded-md border border-input px-3 py-2 bg-background"
      >
        <option value="">Select Bank Account</option>
        {accounts.map((acct) => (
          <option key={acct.id} value={acct.id}>
            {acct.name}
          </option>
        ))}
      </select>

      {transactions.length > 0 && (
        <div className="border rounded-lg overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="bg-muted">
                <th className="text-left p-3">Date</th>
                <th className="text-left p-3">Description</th>
                <th className="text-right p-3">Amount</th>
                <th className="text-center p-3">Status</th>
                <th className="text-right p-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((txn) => (
                <tr key={txn.id} className="border-t">
                  <td className="p-3">{txn.txn_date || txn.date}</td>
                  <td className="p-3">{txn.description}</td>
                  <td className="p-3 text-right">{formatCurrency(txn.amount)}</td>
                  <td className="p-3 text-center">
                    <span className={`px-2 py-1 rounded text-xs ${
                      txn.status === "reconciled" ? "bg-green-100 text-green-800" :
                      txn.status === "cleared" ? "bg-blue-100 text-blue-800" :
                      "bg-gray-100 text-gray-800"
                    }`}>
                      {txn.status}
                    </span>
                  </td>
                  <td className="p-3 text-right">
                    {txn.status !== "reconciled" && (
                      <button
                        className="text-sm text-primary hover:underline flex items-center gap-1"
                        onClick={() => handleReconcile(txn)}
                      >
                        <RefreshCw className="h-3 w-3" />
                        Reconcile
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
