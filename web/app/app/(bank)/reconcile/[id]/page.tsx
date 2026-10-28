"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { BankAccount, BankTransaction } from "@/types/api"

export default function ReconcilePage() {
  const [accounts, setAccounts] = useState<BankAccount[]>([])
  const [selectedAccount, setSelectedAccount] = useState<string | null>(null)
  const [transactions, setTransactions] = useState<BankTransaction[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem("access_token")
    if (!token) {
      window.location.href = "/login"
      return
    }
    api.setToken(token)
    api.get<BankAccount[]>("/bank/accounts")
      .then(setAccounts)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (selectedAccount) {
      api.get<BankTransaction[]>(`/bank/transactions?bank_account_id=${selectedAccount}`)
        .then(setTransactions)
        .catch(console.error)
    }
  }, [selectedAccount])

  if (loading) return <div>Loading...</div>

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Bank Reconciliation</h1>

      <select
        value={selectedAccount || ""}
        onChange={(e) => setSelectedAccount(e.target.value)}
        className="rounded-md border border-input px-3 py-2"
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
          <table className="w-full border-collapse">
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
                  <td className="p-3">{txn.date}</td>
                  <td className="p-3">{txn.description}</td>
                  <td className="p-3 text-right">${txn.amount}</td>
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
                    <button className="text-sm text-primary hover:underline">
                      {txn.matched ? "View" : "Match"}
                    </button>
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
