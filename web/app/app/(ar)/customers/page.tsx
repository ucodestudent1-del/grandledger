"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { Contact } from "@/types/api"

export default function CustomersPage() {
  const [customers, setCustomers] = useState<Contact[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem("access_token")
    if (!token) {
      window.location.href = "/login"
      return
    }
    api.setToken(token)
    api.get<Contact[]>("/contacts?type=customer")
      .then(setCustomers)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div>Loading...</div>

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Customers</h1>
        <button className="bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm">
          Add Customer
        </button>
      </div>
      <div className="border rounded-lg overflow-hidden">
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-muted">
              <th className="text-left p-3">Name</th>
              <th className="text-left p-3">Email</th>
              <th className="text-left p-3">Phone</th>
            </tr>
          </thead>
          <tbody>
            {customers.map((c) => (
              <tr key={c.id} className="border-t">
                <td className="p-3">{c.name}</td>
                <td className="p-3">{c.email || "-"}</td>
                <td className="p-3">{c.phone || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
