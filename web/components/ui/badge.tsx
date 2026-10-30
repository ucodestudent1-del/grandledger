import { forwardRef } from "react"
import { cn } from "@/lib/utils"

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "secondary" | "destructive" | "outline"
}

const badgeVariants = "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors"

export const badgeVariantClasses = {
  default: "bg-primary text-primary-foreground",
  secondary: "bg-secondary text-secondary-foreground",
  destructive: "bg-destructive text-destructive-foreground",
  outline: "border border-input bg-background text-foreground",
}

const Badge = forwardRef<HTMLSpanElement, BadgeProps>(({ className, variant = "default", ...props }, ref) => (
  <span
    ref={ref}
    className={cn(badgeVariants, badgeVariantClasses[variant], className)}
    {...props}
  />
))
Badge.displayName = "Badge"

export { Badge }
