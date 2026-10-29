import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import {
  LayoutDashboard,
  BookOpen,
  FileText,
  Users,
  Receipt,
  ShoppingCart,
  Banknote,
  RefreshCw,
  BarChart3,
  Shield,
  Settings,
} from "lucide-react"

const navigation = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Chart of Accounts", href: "/accounting/chart-of-accounts", icon: BookOpen },
  { name: "Journals", href: "/accounting/journals", icon: FileText },
  { name: "Customers", href: "/customers", icon: Users },
  { name: "Invoices", href: "/invoices", icon: Receipt },
  { name: "Vendors", href: "/vendors", icon: ShoppingCart },
  { name: "Bills", href: "/bills", icon: FileText },
  { name: "Bank Accounts", href: "/bank/accounts", icon: Banknote },
  { name: "Reconciliation", href: "/reconcile", icon: RefreshCw },
  { name: "Reports", href: "/reports/profit-loss", icon: BarChart3 },
  { name: "Audit Log", href: "/audit", icon: Shield },
  { name: "Settings", href: "/settings/company", icon: Settings },
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
              "flex items-center gap-3 px-3 py-2 text-sm rounded-md hover:bg-accent hover:text-accent-foreground transition-colors",
              pathname === item.href && "bg-accent text-accent-foreground"
            )}
          >
            <item.icon className="h-4 w-4" />
            {item.name}
          </Link>
        ))}
      </div>
    </nav>
  )
}
