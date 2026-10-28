"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { useAuth, formatCurrency } from "@/app/hooks/useAuth"
import { Account } from "@/types/api"
import { Loader2, Plus } from "lucide-react"

export default function ChartOfAccountsPage() {
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [accounts, setAccounts] = useState<Account[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!isAuthenticated) return
    api.get<Account[]>("/accounts")
      .then(setAccounts)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [isAuthenticated])

  if (authLoading) return <div className="p-6">Loading...</div>
  if (!isAuthenticated) return null
  if (loading) return <div className="p-6">Loading accounts...</div>

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Chart of Accounts</h1>
        <button className="bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm flex items-center gap-2">
          <Plus className="h-4 w-4" />
          Add Account
        </button>
      </div>

      <div className="border rounded-lg overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-muted">
              <th className="text-left p-3">Code</th>
              <th className="text-left p-3">Name</th>
              <th className="text-left p-3">Type</th>
              <th className="text-right p-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {accounts.map((acct) => (
              <tr key={acct.id} className="border-t">
                <td className="p-3 font-mono">{acct.code}</td>
                <td className="p-3">{acct.name}</td>
                <td className="p-3 capitalize">{acct.type}</td>
                <td className="p-3 text-right">
                  <button className="text-sm text-primary hover:underline">Edit</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
