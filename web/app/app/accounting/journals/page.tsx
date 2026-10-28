"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { JournalEntry } from "@/types/api"

export default function JournalsPage() {
  const [journals, setJournals] = useState<JournalEntry[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem("access_token")
    if (!token) {
      window.location.href = "/login"
      return
    }
    api.setToken(token)

    api.get<JournalEntry[]>("/journals")
      .then(setJournals)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div>Loading...</div>

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Journal Entries</h1>
        <button
          className="bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm"
          onClick={() => (window.location.href = "/app/accounting/journals/new")}
        >
          New Journal Entry
        </button>
      </div>

      <div className="border rounded-lg overflow-hidden">
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-muted">
              <th className="text-left p-3">Number</th>
              <th className="text-left p-3">Date</th>
              <th className="text-left p-3">Description</th>
              <th className="text-left p-3">Status</th>
              <th className="text-right p-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {journals.map((je) => (
              <tr key={je.id} className="border-t">
                <td className="p-3 font-mono">{je.number}</td>
                <td className="p-3">{je.entry_date}</td>
                <td className="p-3">{je.description}</td>
                <td className="p-3">
                  <span className={`px-2 py-1 rounded text-xs ${
                    je.status === "posted" ? "bg-green-100 text-green-800" :
                    je.status === "draft" ? "bg-yellow-100 text-yellow-800" :
                    "bg-gray-100 text-gray-800"
                  }`}>
                    {je.status}
                  </span>
                </td>
                <td className="p-3 text-right">
                  <button
                    className="text-sm text-primary hover:underline"
                    onClick={() => (window.location.href = `/app/accounting/journals/${je.id}`)}
                  >
                    View
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
