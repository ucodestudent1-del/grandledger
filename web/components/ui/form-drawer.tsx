"use client"

import { forwardRef } from "react"
import { cn } from "@/lib/utils"

export interface FormDrawerProps {
  open: boolean
  onClose: () => void
  title: string
  description?: string
  children: React.ReactNode
  footer?: React.ReactNode
  width?: "sm" | "md" | "lg" | "xl"
}

const widthClasses = {
  sm: "max-w-sm",
  md: "max-w-md",
  lg: "max-w-lg",
  xl: "max-w-xl",
}

export function FormDrawer({
  open,
  onClose,
  title,
  description,
  children,
  footer,
  width = "md",
}: FormDrawerProps) {
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm">
      <div
        className="fixed bottom-0 z-50 grid w-full gap-4 border-t bg-background p-6 sm:rounded-t-[14px] sm:h-auto sm:max-w-2xl sm:bottom-auto sm:left-1/2 sm:-translate-x-1/2 sm:translate-y-0 sm:m-6"
      >
        <div className={cn("mx-auto flex flex-col gap-2", widthClasses[width])}>
          <h2 className="text-lg font-semibold">{title}</h2>
          {description && <p className="text-sm text-muted-foreground">{description}</p>}
        </div>
        <div className={cn("mx-auto w-full", widthClasses[width])}>
          {children}
        </div>
        {footer && (
          <div className={cn("mx-auto flex w-full justify-end gap-2 pb-2", widthClasses[width])}>
            {footer}
          </div>
        )}
        <button
          onClick={onClose}
          className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100"
        >
          ✕
        </button>
      </div>
    </div>
  )
}
