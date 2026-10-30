"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { api } from "@/lib/api"
import { useAuth } from "@/app/hooks/useAuth"
import { JournalEntry } from "@/types/api"
import { Loader2, Plus, FileText, Eye, Loader } from "lucide-react"
import { format } from "date-fns"

export default function JournalsPage() {
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [journals, setJournals] = useState<JournalEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [postingId, setPostingId] = useState<string | null>(null)
  const [voidingId, setVoidingId] = useState<string | null>(null)

  useEffect(() => {
    if (!isAuthenticated) return
    api.get<JournalEntry[]>("/journals?page=1&page_size=50")
      .then(setJournals)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [isAuthenticated])

  const handlePost = async (jeId: string) => {
    setPostingId(jeId)
    try {
      await api.post(`/journals/${jeId}/post`, {})
      setJournals(journals.map((j) =>
        j.id === jeId ? { ...j, status: "posted", posted_at: new Date().toISOString() } : j
      ))
    } catch (err: any) {
      console.error("Failed to post:", err)
    } finally {
      setPostingId(null)
    }
  }

  const handleVoid = async (jeId: string) => {
    setVoidingId(jeId)
    try {
      await api.post(`/journals/${jeId}/void`, {})
      setJournals(journals.map((j) =>
        j.id === jeId ? { ...j, status: "void" } : j
      ))
    } catch (err: any) {
      console.error("Failed to void:", err)
    } finally {
      setVoidingId(null)
    }
  }

  const handleReverse = async (jeId: string) => {
    try {
      await api.post(`/journals/${jeId}/reverse`, {})
      // Refresh list to show the new reversal entry
      api.get<JournalEntry[]>("/journals?page=1&page_size=50")
        .then(setJournals)
        .catch(console.error)
    } catch (err: any) {
      console.error("Failed to reverse:", err)
    }
  }

  if (authLoading) return <div className="p-6">Loading...</div>
  if (!isAuthenticated) return null
  if (loading) return <div className="p-6">Loading journal entries...</div>

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Journal Entries</h1>
        <Link
          href="/accounting/journals/new"
          className="bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          New Journal Entry
        </Link>
      </div>

      <div className="border rounded-lg overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-muted">
              <th className="text-left p-3">Number</th>
              <th className="text-left p-3">Date</th>
              <th className="text-left p-3">Description</th>
              <th className="text-center p-3">Status</th>
              <th className="text-right p-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {journals.length === 0 ? (
              <tr>
                <td colSpan={5} className="p-4 text-center text-muted-foreground">
                  No journal entries found. Create your first entry to get started.
                </td>
              </tr>
            ) : (
              journals.map((je) => (
                <tr key={je.id} className="border-t">
                  <td className="p-3 font-mono">{je.number}</td>
                  <td className="p-3 text-sm">{je.entry_date ? format(new Date(je.entry_date), "PP") : "-"}</td>
                  <td className="p-3">{je.description || "-"}</td>
                  <td className="p-3 text-center">
                    <span className={`px-2 py-1 rounded text-xs capitalize ${
                      je.status === "posted" ? "bg-green-100 text-green-800" :
                      je.status === "draft" ? "bg-yellow-100 text-yellow-800" :
                      "bg-gray-100 text-gray-800"
                    }`}>
                      {je.status}
                    </span>
                  </td>
                  <td className="p-3 text-right space-x-1">
                    <Link href={`/accounting/journals/${je.id}`} className="text-primary hover:underline text-sm">
                      View
                    </Link>
                    {je.status === "draft" && (
                      <button
                        onClick={() => handlePost(je.id)}
                        disabled={postingId === je.id}
                        className="text-blue-600 hover:text-blue-800 text-sm disabled:opacity-50"
                      >
                        {postingId === je.id ? "Posting..." : "Post"}
                      </button>
                    )}
                    {je.status === "posted" && (
                      <>
                        <button
                          onClick={() => handleReverse(je.id)}
                          className="text-orange-600 hover:text-orange-800 text-sm"
                        >
                          Reverse
                        </button>
                        <button
                          onClick={() => handleVoid(je.id)}
                          disabled={voidingId === je.id}
                          className="text-red-600 hover:text-red-800 text-sm disabled:opacity-50"
                        >
                          {voidingId === je.id ? "Voiding..." : "Void"}
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
