"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { AuditLog } from "@/types/api"

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem("access_token")
    if (!token) {
      window.location.href = "/login"
      return
    }
    api.setToken(token)
    api.get<AuditLog[]>("/audit/logs")
      .then(setLogs)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div>Loading...</div>

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Audit Log</h1>
      <div className="border rounded-lg overflow-hidden">
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-muted">
              <th className="text-left p-3">Date</th>
              <th className="text-left p-3">Action</th>
              <th className="text-left p-3">Entity</th>
              <th className="text-left p-3">IP</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr key={log.id} className="border-t">
                <td className="p-3 text-sm">{new Date(log.created_at).toLocaleString()}</td>
                <td className="p-3 text-sm">{log.action}</td>
                <td className="p-3 text-sm">{log.entity_type}</td>
                <td className="p-3 text-sm">{log.ip_address || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
