"use client"

import { ReactNode } from "react"
import { cn } from "@/lib/utils"
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from "lucide-react"

export interface Column<T> {
  key: string
  header: string
  render?: (row: T) => ReactNode
  className?: string
}

export interface DataTableProps<T> {
  data: T[]
  columns: Column<T>[]
  pageSize?: number
  pageSizeOptions?: number[]
  onPageChange?: (page: number) => void
  emptyMessage?: string
  className?: string
}

export function DataTable<T>({
  data,
  columns,
  pageSize = 10,
  pageSizeOptions = [10, 20, 30, 50],
  onPageChange,
  emptyMessage = "No data available",
  className,
}: DataTableProps<T>) {
  const [page, setPage] = useState(0)
  const [currentPageSize, setCurrentPageSize] = useState(pageSize)

  const startIndex = page * currentPageSize
  const endIndex = startIndex + currentPageSize
  const pagedData = data.slice(startIndex, endIndex)
  const pageCount = Math.ceil(data.length / currentPageSize)

  const handlePageChange = (newPage: number) => {
    setPage(Math.max(0, Math.min(newPage, Math.max(0, pageCount - 1))))
    onPageChange?.(page)
  }

  const handlePageSizeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setCurrentPageSize(Number(e.target.value))
    setPage(0)
  }

  return (
    <div className={cn("space-y-4", className)}>
      <div className="overflow-x-auto rounded-md border">
        <table className="w-full caption-bottom text-sm">
          <thead className="bg-muted/50">
            <tr>
              {columns.map((column) => (
                <th
                  key={column.key}
                  className={cn("text-left align-middle font-medium p-3", column.className)}
                >
                  {column.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pagedData.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="p-6 text-center text-muted-foreground">
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              pagedData.map((row, rowIndex) => (
                <tr key={rowIndex} className={rowIndex % 2 ? "bg-muted/25" : ""}>
                  {columns.map((column) => (
                    <td key={column.key} className={cn("p-3 align-middle", column.className)}>
                      {column.render ? column.render(row) : (row as any)[column.key]}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="text-sm text-muted-foreground">
            {data.length} row(s) total
          </span>
          <select
            value={currentPageSize}
            onChange={handlePageSizeChange}
            className="h-8 w-[70px] border border-input rounded bg-background"
          >
            {pageSizeOptions.map((size) => (
              <option key={size} value={size}>
                {size} / page
              </option>
            ))}
          </select>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => handlePageChange(0)}
            disabled={page === 0}
            className="h-8 w-8 p-0 border border-input rounded disabled:opacity-50"
          >
            <ChevronsLeft className="h-4 w-4 mx-auto" />
          </button>
          <button
            onClick={() => handlePageChange(page - 1)}
            disabled={page === 0}
            className="h-8 w-8 p-0 border border-input rounded disabled:opacity-50"
          >
            <ChevronLeft className="h-4 w-4 mx-auto" />
          </button>
          <span className="text-sm">
            Page {page + 1} of {Math.max(1, pageCount)}
          </span>
          <button
            onClick={() => handlePageChange(page + 1)}
            disabled={page >= pageCount - 1}
            className="h-8 w-8 p-0 border border-input rounded disabled:opacity-50"
          >
            <ChevronRight className="h-4 w-4 mx-auto" />
          </button>
          <button
            onClick={() => handlePageChange(pageCount - 1)}
            disabled={page >= pageCount - 1}
            className="h-8 w-8 p-0 border border-input rounded disabled:opacity-50"
          >
            <ChevronsRight className="h-4 w-4 mx-auto" />
          </button>
        </div>
      </div>
    </div>
  )
}

import { useState } from "react"
