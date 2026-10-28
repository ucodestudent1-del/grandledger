"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { useAuth } from "@/app/hooks/useAuth"
import { User } from "@/types/api"
import { Plus, Mail, User as UserIcon, Shield } from "lucide-react"

export default function UsersPage() {
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!isAuthenticated) return
    api.get<User[]>("/users")
      .then(setUsers)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [isAuthenticated])

  if (authLoading) return <div className="p-6">Loading...</div>
  if (!isAuthenticated) return null
  if (loading) return <div className="p-6">Loading users...</div>

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Team Members</h1>
        <button className="bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm flex items-center gap-2">
          <Plus className="h-4 w-4" />
          Invite User
        </button>
      </div>

      <div className="border rounded-lg overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-muted">
              <th className="text-left p-3">Name</th>
              <th className="text-left p-3">Email</th>
              <th className="text-left p-3">Role</th>
              <th className="text-left p-3">External Accountant</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-t">
                <td className="p-3 flex items-center gap-2">
                  <UserIcon className="h-4 w-4 text-muted-foreground" />
                  {u.name}
                </td>
                <td className="p-3 flex items-center gap-2">
                  <Mail className="h-4 w-4 text-muted-foreground" />
                  {u.email}
                </td>
                <td className="p-3 capitalize">
                  <span className="inline-flex items-center gap-1">
                    <Shield className="h-3 w-3" />
                    {u.role}
                  </span>
                </td>
                <td className="p-3">{u.is_external_accountant ? "Yes" : "No"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
