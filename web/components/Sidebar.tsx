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

interface NavItem {
  name: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  submenu?: { name: string; href: string }[]
}

const navigation: NavItem[] = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Chart of Accounts", href: "/accounting/chart-of-accounts", icon: BookOpen },
  { name: "Journals", href: "/accounting/journals", icon: FileText },
  { name: "Customers", href: "/customers", icon: Users },
  { name: "Invoices", href: "/invoices", icon: Receipt },
  { name: "Vendors", href: "/vendors", icon: ShoppingCart },
  { name: "Bills", href: "/bills", icon: FileText },
  { name: "Payments", href: "/payments", icon: Banknote },
  { name: "Bank Accounts", href: "/bank/accounts", icon: Banknote },
  { name: "Reconciliation", href: "/bank/reconcile", icon: RefreshCw },
  {
    name: "Reports",
    href: "/reports/profit-loss",
    icon: BarChart3,
    submenu: [
      { name: "Profit & Loss", href: "/reports/profit-loss" },
      { name: "Balance Sheet", href: "/reports/balance-sheet" },
      { name: "Trial Balance", href: "/reports/trial-balance" },
      { name: "General Ledger", href: "/reports/general-ledger" },
      { name: "AR Aging", href: "/reports/ar-aging" },
      { name: "AP Aging", href: "/reports/ap-aging" },
    ],
  },
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
          <div key={item.href}>
            <Link
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 text-sm rounded-md hover:bg-accent hover:text-accent-foreground transition-colors",
                pathname === item.href && "bg-accent text-accent-foreground",
              )}
            >
              <item.icon className="h-4 w-4" />
              {item.name}
            </Link>
            {item.submenu && pathname.startsWith("/reports") && (
              <div className="ml-6 mt-1 space-y-1">
                {item.submenu.map((sub) => (
                  <Link
                    key={sub.href}
                    href={sub.href}
                    className={cn(
                      "flex items-center gap-3 px-3 py-1 text-sm rounded-md hover:bg-accent hover:text-accent-foreground transition-colors",
                      pathname === sub.href && "bg-accent text-accent-foreground",
                    )}
                  >
                    {sub.name}
                  </Link>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </nav>
  )
}
