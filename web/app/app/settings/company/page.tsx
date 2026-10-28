"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { Company } from "@/types/api"

export default function CompanySettingsPage() {
  const [company, setCompany] = useState<Company | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem("access_token")
    if (!token) {
      window.location.href = "/login"
      return
    }
    api.setToken(token)
    api.get<Company[]>("/companies")
      .then((res) => {
        if (res.length > 0) setCompany(res[0])
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div>Loading...</div>

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Company Settings</h1>
      {company && (
        <div className="border rounded-lg p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium">Name</label>
            <p className="mt-1">{company.name}</p>
          </div>
          <div>
            <label className="block text-sm font-medium">Slug</label>
            <p className="mt-1">{company.slug}</p>
          </div>
          <div>
            <label className="block text-sm font-medium">Currency</label>
            <p className="mt-1">{company.currency}</p>
          </div>
        </div>
      )}
    </div>
  )
}
