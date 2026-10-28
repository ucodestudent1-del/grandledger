"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { useAuth } from "@/app/hooks/useAuth"
import { AuditLog } from "@/types/api"
import { format } from "date-fns"

export default function AuditPage() {
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)

  useEffect(() => {
    if (!isAuthenticated) return
    api.get<{ items: AuditLog[]; pagination: { total_pages: number } }>(
      `/audit/logs?page=${page}&page_size=50`
    )
      .then((res) => {
        setLogs(res.items)
        setTotalPages(res.pagination.total_pages)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [isAuthenticated, page])

  if (authLoading) return <div className="p-6">Loading...</div>
  if (!isAuthenticated) return null
  if (loading) return <div className="p-6">Loading audit logs...</div>

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Audit Log</h1>

      <div className="border rounded-lg overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-muted">
              <th className="text-left p-3">Date</th>
              <th className="text-left p-3">Action</th>
              <th className="text-left p-3">Entity Type</th>
              <th className="text-left p-3">Entity ID</th>
              <th className="text-left p-3">User ID</th>
              <th className="text-left p-3">IP Address</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr key={log.id} className="border-t">
                <td className="p-3 text-sm">{format(new Date(log.created_at), "PPpp")}</td>
                <td className="p-3 text-sm font-mono">{log.action}</td>
                <td className="p-3 text-sm">{log.entity_type}</td>
                <td className="p-3 text-sm font-mono">{log.entity_id || "-"}</td>
                <td className="p-3 text-sm font-mono">{log.user_id || "-"}</td>
                <td className="p-3 text-sm">{log.ip_address || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex justify-between items-center">
        <button
          onClick={() => setPage(Math.max(1, page - 1))}
          disabled={page <= 1}
          className="px-3 py-1 border rounded disabled:opacity-50"
        >
          Previous
        </button>
        <span className="text-sm text-muted-foreground">
          Page {page} of {totalPages}
        </span>
        <button
          onClick={() => setPage(Math.min(totalPages, page + 1))}
          disabled={page >= totalPages}
          className="px-3 py-1 border rounded disabled:opacity-50"
        >
          Next
        </button>
      </div>
    </div>
  )
}
