"use client"

import Link from "next/link"
import {
  BookOpen,
  CreditCard,
  FileText,
  Globe,
  Hash,
  Lock,
  Receipt,
  RefreshCw,
  Shield,
  Users,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardTitle } from "@/components/ui/card"

const features = [
  {
    title: "Immutable Double-Entry Ledger",
    description:
      "Every transaction is validated so debits always equal credits. Posted entries cannot be edited—corrections are handled with reversing entries and a full audit trail.",
    icon: Hash,
  },
  {
    title: "Sales & Invoicing (AR)",
    description:
      "Create professional invoices with PDF export, accept full or partial payments, issue credit notes, and track receivables with real-time AR aging reports.",
    icon: Receipt,
  },
  {
    title: "Purchases & Bills (AP)",
    description:
      "Record vendor bills, make full or partial payments, handle debit notes, and keep an eye on what you owe with AP aging reports.",
    icon: CreditCard,
  },
  {
    title: "Bank Reconciliation",
    description:
      "Import bank CSV statements, automatically match transactions to journal entries, and reconcile your accounts with confidence.",
    icon: RefreshCw,
  },
  {
    title: "Audit-Ready Reports",
    description:
      "Generate Profit & Loss, Balance Sheet, Trial Balance, General Ledger, and aging reports in seconds—all exportable as PDF.",
    icon: FileText,
  },
  {
    title: "Multi-Tenant Security",
    description:
      "Built-in tenant isolation, JWT auth with rotating refresh tokens, role-based access control, and an immutable audit log of every ledger mutation.",
    icon: Shield,
  },
]

const stats = [
  { label: "Journal Entries", value: "5+", icon: BookOpen },
  { label: "Financial Reports", value: "6+", icon: FileText },
  { label: "Integrations", value: "3+", icon: Globe },
]

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="container mx-auto flex h-16 items-center justify-between px-4">
        <Link href="/" className="text-2xl font-bold">
          GrandLedger
        </Link>
        <nav className="flex items-center gap-4">
          <Link href="/landing#features">Features</Link>
          <Link href="/login">Login</Link>
          <Button asChild>
            <Link href="/signup">Start Free Trial</Link>
          </Button>
        </nav>
      </header>

      <main className="flex-1">
        <section className="container mx-auto px-4 py-20 text-center">
          <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl">
            Bookkeeping, simplified.
          </h1>
          <p className="mt-4 text-lg text-muted-foreground">
            A multi-tenant, audit-ready double-entry ledger built for freelancers,
            small businesses, and accountants managing multiple clients.
          </p>
          <div className="mt-8 flex justify-center gap-4">
            <Button size="lg" asChild>
              <Link href="/signup">Get Started</Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link href="/login">Sign In</Link>
            </Button>
          </div>
        </section>

        <section
          id="features"
          className="container mx-auto grid gap-y-12 px-4 py-16 sm:grid-cols-2 lg:grid-cols-3"
        >
          {features.map((feature) => (
            <Card key={feature.title} className="flex flex-col">
              <CardContent className="pt-6">
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                  <feature.icon className="h-6 w-6 text-primary" />
                </div>
                <CardTitle className="mb-2 text-xl">{feature.title}</CardTitle>
                <CardDescription>{feature.description}</CardDescription>
              </CardContent>
            </Card>
          ))}
        </section>

        <section className="container mx-auto px-4 py-16">
          <h2 className="text-center text-2xl font-bold">Trusted by finance teams</h2>
          <div className="mt-12 grid justify-center gap-8 sm:grid-cols-3">
            {stats.map((stat) => (
              <div key={stat.label} className="text-center">
                <div className="flex justify-center">
                  <stat.icon className="h-8 w-8 text-primary" />
                </div>
                <div className="mt-2 text-3xl font-bold">{stat.value}</div>
                <div className="text-sm text-muted-foreground">{stat.label}</div>
              </div>
            ))}
          </div>
        </section>

        <section className="container mx-auto px-4 py-20 text-center">
          <h2 className="text-3xl font-bold">Ready to get started?</h2>
          <p className="mt-4 text-muted-foreground">
            No credit card required. Start your 14-day free trial today.
          </p>
          <div className="mt-8">
            <Button size="lg" asChild>
              <Link href="/signup">Create Your Account</Link>
            </Button>
          </div>
        </section>
      </main>

      <footer className="border-t py-8">
        <div className="container mx-auto flex flex-col items-center justify-between gap-4 px-4 text-sm text-muted-foreground">
        <div className="flex items-center gap-2">
        <Lock className="h-4 w-4" />
        <span>Bank-level encryption</span>
      </div>
      <nav className="flex gap-6">
        <Link href="/landing#features" className="hover:text-foreground">Features</Link>
        <Link href="/login" className="hover:text-foreground">Login</Link>
        <Link href="/signup" className="hover:text-foreground">Sign Up</Link>
      </nav>
      <p>&copy; {new Date().getFullYear()} GrandLedger. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}
