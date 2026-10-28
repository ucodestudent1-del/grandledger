"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { BankAccount } from "@/types/api"

export default function BankAccountsPage() {
  const [accounts, setAccounts] = useState<BankAccount[]>([])
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

  if (loading) return <div>Loading...</div>

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Bank Accounts</h1>
        <button className="bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm">
          Add Bank Account
        </button>
      </div>
      <div className="border rounded-lg overflow-hidden">
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-muted">
              <th className="text-left p-3">Name</th>
              <th className="text-left p-3">Bank</th>
              <th className="text-left p-3">Account #</th>
              <th className="text-right p-3">Balance</th>
            </tr>
          </thead>
          <tbody>
            {accounts.map((acct) => (
              <tr key={acct.id} className="border-t">
                <td className="p-3">{acct.name}</td>
                <td className="p-3">{acct.bank_name || "-"}</td>
                <td className="p-3">{acct.account_number || "-"}</td>
                <td className="p-3 text-right">${acct.starting_balance}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
