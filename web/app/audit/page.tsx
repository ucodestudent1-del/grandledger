"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { useAuth } from "@/app/hooks/useAuth"
import { AuditLog } from "@/types/api"
import { format } from "date-fns"
import { JsonDiff } from "@/components/audit/JsonDiff"

export default function AuditPage() {
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [entityTypeFilter, setEntityTypeFilter] = useState("")
  const [actionFilter, setActionFilter] = useState("")
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null)

  useEffect(() => {
    if (!isAuthenticated) return
    const params = new URLSearchParams({
      page: String(page),
      page_size: "50",
      ...(entityTypeFilter && { entity_type: entityTypeFilter }),
      ...(actionFilter && { action: actionFilter }),
    })
    api.get<{ items: AuditLog[]; pagination: { total_pages: number } }>(
      `/audit/logs?${params.toString()}`
    )
      .then((res) => {
        setLogs(res.items)
        setTotalPages(res.pagination.total_pages)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [isAuthenticated, page, entityTypeFilter, actionFilter])

  if (authLoading) return <div className="p-6">Loading...</div>
  if (!isAuthenticated) return null

  return (
    <div className="space-y-4">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Audit Log</h1>
          <p className="text-muted-foreground">
            Immutable record of every ledger mutation in this company.
          </p>
        </div>
        <button
          onClick={() => {
            const url = `/audit/logs/export?${new URLSearchParams({
              ...(entityTypeFilter && { entity_type: entityTypeFilter }),
              ...(actionFilter && { action: actionFilter }),
            }).toString()}`
            window.location.href = url
          }}
          className="px-4 py-2 border border-input bg-background hover:bg-accent rounded-md text-sm"
        >
          Export CSV
        </button>
      </div>

      <div className="flex gap-2">
        <input
          type="text"
          placeholder="Filter by entity type..."
          value={entityTypeFilter}
          onChange={(e) => { setEntityTypeFilter(e.target.value); setPage(1) }}
          className="border border-input rounded px-3 py-1.5 text-sm focus:ring-1 focus:ring-ring"
        />
        <input
          type="text"
          placeholder="Filter by action..."
          value={actionFilter}
          onChange={(e) => { setActionFilter(e.target.value); setPage(1) }}
          className="border border-input rounded px-3 py-1.5 text-sm focus:ring-1 focus:ring-ring"
        />
      </div>

      {selectedLog && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-background border rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="text-lg font-semibold">Audit Detail</h2>
              <button
                onClick={() => setSelectedLog(null)}
                className="text-muted-foreground hover:text-destructive"
              >
                Close
              </button>
            </div>
            <div className="p-4 overflow-y-auto max-h-[60vh] space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div><span className="font-mono text-muted-foreground">Action:</span> {selectedLog.action}</div>
                <div><span className="font-mono text-muted-foreground">Entity:</span> {selectedLog.entity_type}</div>
                <div><span className="font-mono text-muted-foreground">Entity ID:</span> {selectedLog.entity_id || "-"}</div>
                <div><span className="font-mono text-muted-foreground">User ID:</span> {selectedLog.user_id || "-"}</div>
                <div><span className="font-mono text-muted-foreground">IP:</span> {selectedLog.ip_address || "-"}</div>
                <div><span className="font-mono text-muted-foreground">Date:</span> {format(new Date(selectedLog.created_at), "PPpp")}</div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="border rounded p-3">
                  <h3 className="text-sm font-medium mb-2 text-destructive">Before</h3>
                  <JsonDiff data={selectedLog.before ?? {}} />
                </div>
                <div className="border rounded p-3">
                  <h3 className="text-sm font-medium mb-2 text-green-700">After</h3>
                  <JsonDiff data={selectedLog.after ?? {}} />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="border rounded-lg overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-muted">
              <th className="text-left p-3">Date</th>
              <th className="text-left p-3">Action</th>
              <th className="text-left p-3">Entity Type</th>
              <th className="text-left p-3">Entity ID</th>
              <th className="text-left p-3">User</th>
              <th className="text-left p-3">IP</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr
                key={log.id}
                className="border-t cursor-pointer hover:bg-muted/50"
                onClick={() => setSelectedLog(log)}
              >
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
