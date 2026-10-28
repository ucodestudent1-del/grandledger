"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { useAuth, formatCurrency } from "@/app/hooks/useAuth"
import { BankAccount, BankTransaction } from "@/types/api"
import { Plus, Upload, RefreshCw } from "lucide-react"

export default function BankAccountsPage() {
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [accounts, setAccounts] = useState<BankAccount[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!isAuthenticated) return
    api.get<BankAccount[]>("/bank/accounts")
      .then(setAccounts)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [isAuthenticated])

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
                  <button
                    className="text-sm text-primary hover:underline"
                    onClick={() => (window.location.href = `/bank/accounts/${acct.id}`)}
                  >
                    Manage
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}


