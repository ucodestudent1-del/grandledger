import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"

const navigation = [
  { name: "Dashboard", href: "/app" },
  { name: "Chart of Accounts", href: "/app/accounting/chart-of-accounts" },
  { name: "Journals", href: "/app/accounting/journals" },
  { name: "Customers", href: "/app/ar/customers" },
  { name: "Invoices", href: "/app/ar/invoices" },
  { name: "Vendors", href: "/app/ap/vendors" },
  { name: "Bills", href: "/app/ap/bills" },
  { name: "Banking", href: "/app/bank/accounts" },
  { name: "Reports", href: "/app/reports/profit-loss" },
  { name: "Audit Log", href: "/app/audit" },
]

export default function Sidebar() {
  const pathname = usePathname()

  return (
    <nav className="flex flex-col w-64 bg-card border-r h-screen overflow-y-auto">
      <div className="p-4 border-b">
        <h1 className="text-xl font-bold">GrandLedger</h1>
      </div>
      <div className="flex-1 p-2">
        {navigation.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex items-center px-3 py-2 text-sm rounded-md hover:bg-accent hover:text-accent-foreground transition-colors",
              pathname === item.href && "bg-accent text-accent-foreground"
            )}
          >
            {item.name}
          </Link>
        ))}
      </div>
    </nav>
  )
}
