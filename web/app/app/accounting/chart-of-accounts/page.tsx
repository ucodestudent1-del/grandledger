"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { Account } from "@/types/api"

export default function ChartOfAccountsPage() {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem("access_token")
    if (!token) {
      window.location.href = "/login"
      return
    }
    api.setToken(token)

    api.get<Account[]>("/accounts")
      .then(setAccounts)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div>Loading...</div>

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Chart of Accounts</h1>
        <button className="bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm">
          Add Account
        </button>
      </div>

      <div className="border rounded-lg overflow-hidden">
        <table className="w-full border-collapse">
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
