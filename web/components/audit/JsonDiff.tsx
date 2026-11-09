"use client"

export function JsonDiff({ data }: { data: Record<string, unknown> }) {
  const entries = Object.entries(data)
  if (entries.length === 0) {
    return <span className="text-muted-foreground text-sm italic">(no changes)</span>
  }
  return (
    <ul className="list-disc list-inside text-sm space-y-1 text-muted-foreground">
      {entries.map(([key, value]) => (
        <li key={key} className="flex justify-between">
          <span className="font-mono">{String(key)}:</span>
          <span className="font-mono">
            {typeof value === "object" && value !== null
              ? JSON.stringify(value)
              : String(value ?? "")}
          </span>
        </li>
      ))}
    </ul>
  )
}
