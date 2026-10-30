import { Badge, BadgeProps } from "@/components/ui/badge"

export type StatusType = "draft" | "posted" | "void" | "issued" | "paid" | "partial" | "pending" | "cleared" | "reconciled"

const statusConfig: Record<StatusType, BadgeProps["variant"]> = {
  draft: "outline",
  posted: "default",
  void: "destructive",
  issued: "default",
  paid: "default",
  partial: "secondary",
  pending: "outline",
  cleared: "default",
  reconciled: "default",
}

export { statusConfig }

export default function StatusBadge({ status, children }: { status: StatusType; children?: React.ReactNode }) {
  return (
    <Badge variant={statusConfig[status] || "outline"}>
      {children || status}
    </Badge>
  )
}
