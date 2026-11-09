"use client"

import Link from "next/link"
import {
  ArrowRight,
  BookOpen,
  Check,
  ChevronRight,
  Clock,
  CreditCard,
  FileText,
  Globe,
  Hash,
  Lock,
  Receipt,
  RefreshCw,
  Shield,
  Users,
  Zap,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

const navLinks = [
  { name: "Features", href: "#features" },
  { name: "Pricing", href: "#pricing" },
  { name: "How It Works", href: "#how-it-works" },
  { name: "FAQ", href: "#faq" },
]

const heroStats = [
  { label: "Journal Entries", value: "Double-entry" },
  { label: "Financial Reports", value: "6 types" },
  { label: "Free Trial", value: "14 days" },
]

const features = [
  {
    title: "Immutable Double-Entry Ledger",
    description:
      "Every transaction is validated so debits always equal credits. Posted entries cannot be edited—corrections use reversing entries with a full audit trail.",
    icon: Hash,
  },
  {
    title: "Professional Invoices (AR)",
    description:
      "Create branded invoices, accept full or partial payments, issue credit notes, and track receivables with AR aging reports.",
    icon: Receipt,
  },
  {
    title: "Vendor Bills (AP)",
    description:
      "Record bills, make payments, handle debit notes, and track what you owe with AP aging reports.",
    icon: CreditCard,
  },
  {
    title: "Bank Reconciliation",
    description:
      "Import CSV bank statements, match transactions to journal entries, and reconcile accounts with confidence.",
    icon: RefreshCw,
  },
  {
    title: "Audit-Ready Reports",
    description:
      "Profit & Loss, Balance Sheet, Trial Balance, General Ledger, and aging reports—all exportable as PDF.",
    icon: FileText,
  },
  {
    title: "Multi-Client Security",
    description:
      "Tenant-isolated data, JWT auth with refresh tokens, role-based access, and an immutable audit log.",
    icon: Shield,
  },
]

const howItWorks = [
  {
    step: 1,
    title: "Set up your chart of accounts",
    description:
      "Choose from a default chart of accounts or customize it for your business. All accounts are double-entry ready.",
    icon: BookOpen,
  },
  {
    step: 2,
    title: "Record transactions",
    description:
      "Create invoices, record bills, and log payments. Every entry is validated to keep your books balanced.",
    icon: Zap,
  },
  {
    step: 3,
    title: "Generate reports",
    description:
      "Run Profit & Loss, Balance Sheet, and Trial Balance reports instantly. Export as PDF for your accountant.",
    icon: FileText,
  },
]

const faqs = [
  {
    q: "Do I need accounting experience?",
    a:
      "No. GrandLedger guides you through double-entry bookkeeping with automatic balancing. If you can use a spreadsheet, you can use GrandLedger.",
  },
  {
    q: "Can I invite my accountant?",
    a:
      "Yes. Invite your accountant as a read-only or full-access user. They get their own login without seeing your billing info.",
  },
  {
    q: "Is my data secure?",
    a:
      "Yes. All data is encrypted in transit and at rest. We use JWT authentication, role-based access control, and PostgreSQL row-level security for tenant isolation.",
  },
  {
    q: "Can I export my data?",
    a:
      "Absolutely. Export any report as PDF or CSV. You own your data and can take it with you anytime.",
  },
  {
    q: "What happens after my trial?",
    a:
      "Your account switches to the free tier with limited features. You can upgrade to Starter or Professional anytime to keep using GrandLedger.",
  },
  {
    q: "Do you offer refunds?",
    a:
      "Yes. Cancel within 30 days of your first payment for a full refund, no questions asked.",
  },
]

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="container mx-auto flex h-16 items-center justify-between px-4">
        <Link href="/" className="text-2xl font-bold tracking-tight">
          GrandLedger
        </Link>
        <nav className="hidden md:flex items-center gap-6">
          {navLinks.map((link) => (
            <Link
              key={link.name}
              href={link.href}
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              {link.name}
            </Link>
          ))}
        </nav>
        <div className="flex items-center gap-3">
          <Link href="/login" className="text-sm text-muted-foreground hover:text-foreground">
            Log in
          </Link>
          <Button asChild>
            <Link href="/pricing">Get Started</Link>
          </Button>
        </div>
      </header>

      <main className="flex-1">
        {/* Hero */}
        <section className="relative overflow-hidden">
          <div className="mx-auto max-w-7xl px-4 py-24 sm:px-6 sm:py-32 lg:px-8">
            <div className="text-center">
              <Badge className="mb-6 inline-flex items-center gap-2 px-3 py-1 rounded-full bg-green-50 text-green-700 text-xs font-semibold border border-green-200">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                </span>
                14-day free trial — no credit card required
              </Badge>
              <h1 className="text-5xl font-extrabold tracking-tight sm:text-6xl">
                Bookkeeping that actually works
              </h1>
              <p className="mt-6 text-lg text-muted-foreground max-w-2xl mx-auto">
                Double-entry bookkeeping built for freelancers, small businesses,
                and accountants managing multiple clients. Audit-ready, immutable,
                and designed for real bookkeeping work—not spreadsheets.
              </p>
              <div className="mt-10 flex flex-col sm:flex-row justify-center gap-4">
                <Button size="lg" className="w-full sm:w-auto" asChild>
                  <Link href="/signup">Start Free Trial</Link>
                </Button>
                <Button size="lg" variant="outline" className="w-full sm:w-auto" asChild>
                  <Link href="/pricing">View Pricing</Link>
                </Button>
              </div>
              <div className="mt-12 flex items-center justify-center gap-6 text-sm text-muted-foreground">
                {heroStats.map((stat) => (
                  <div key={stat.label} className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-muted-foreground" />
                    <span>{stat.label}</span>
                    <span className="mx-1 h-4 w-px bg-muted" />
                    <span className="font-semibold">{stat.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Features */}
        <section id="features" className="container mx-auto px-4 py-24 sm:px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold tracking-tight">Everything you need for clean books</h2>
            <p className="mt-4 text-muted-foreground">
              Powerful double-entry bookkeeping without the complexity of enterprise software.
            </p>
          </div>

          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feature) => (
              <Card key={feature.title} className="hover:shadow-md transition-shadow">
                <div className="p-6">
                  <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                    <feature.icon className="h-6 w-6 text-primary" />
                  </div>
                  <h3 className="text-lg font-semibold">{feature.title}</h3>
                  <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                    {feature.description}
                  </p>
                </div>
              </Card>
            ))}
          </div>
        </section>

        {/* How It Works */}
        <section id="how-it-works" className="container mx-auto px-4 py-24 sm:px-6 bg-muted/50">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold tracking-tight">How it works</h2>
            <p className="mt-4 text-muted-foreground">
              Get your books in order in three steps.
            </p>
          </div>

          <div className="grid gap-12 sm:grid-cols-3">
            {howItWorks.map((step) => (
              <Card key={step.step} className="p-8 text-center">
                <div className="mx-auto mb-6 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                  <step.icon className="h-6 w-6 text-primary" />
                </div>
                <span className="mb-2 block text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Step {step.step}
                </span>
                <h3 className="text-lg font-semibold">{step.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                  {step.description}
                </p>
              </Card>
            ))}
          </div>
        </section>

        {/* Pricing Preview */}
        <section id="pricing" className="container mx-auto px-4 py-24 sm:px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold tracking-tight">Simple, transparent pricing</h2>
            <p className="mt-4 text-muted-foreground">
              Choose the plan that fits your business. All plans include a 14-day free trial.
            </p>
          </div>

          <div className="grid gap-8 sm:grid-cols-3 max-w-6xl mx-auto">
            <Card className="p-8">
              <CardHeader>
                <CardTitle>Starter</CardTitle>
                <CardDescription>For freelancers and solo business owners</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-baseline gap-2">
                  <span className="text-4xl font-bold">$19</span>
                  <span className="text-sm font-semibold text-muted-foreground">/mo</span>
                </div>
                <ul className="space-y-3 text-sm text-muted-foreground">
                  <li className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-green-600" />
                    1 company
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-green-600" />
                    3 users
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-green-600" />
                    Invoicing & payments
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-green-600" />
                    Financial reports
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="line-through text-gray-400">Bank reconciliation</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="line-through text-gray-400">Multi-client access</span>
                  </li>
                </ul>
              </CardContent>
              <CardFooter>
                <Button className="w-full" asChild>
                  <Link href="/signup?plan=starter">Start Free Trial</Link>
                </Button>
              </CardFooter>
            </Card>

            <Card className="p-8 relative border-primary bg-primary/5">
              <Badge className="absolute top-0 right-0 mt-4 mr-4 bg-primary text-primary-foreground px-3 py-1 rounded-full text-xs font-semibold">
                Most Popular
              </Badge>
              <CardHeader>
                <CardTitle>Professional</CardTitle>
                <CardDescription>For growing businesses and bookkeepers</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-baseline gap-2">
                  <span className="text-4xl font-bold">$49</span>
                  <span className="text-sm font-semibold text-muted-foreground">/mo</span>
                </div>
                <ul className="space-y-3 text-sm text-muted-foreground">
                  <li className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-green-600" />
                    5 companies
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-green-600" />
                    10 users
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-green-600" />
                    Invoicing & payments
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-green-600" />
                    Bank reconciliation
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-green-600" />
                    Financial reports
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-green-600" />
                    Accountant access
                  </li>
                </ul>
              </CardContent>
              <CardFooter>
                <Button className="w-full" asChild>
                  <Link href="/signup?plan=professional">Start Free Trial</Link>
                </Button>
              </CardFooter>
            </Card>

            <Card className="p-8">
              <CardHeader>
                <CardTitle>Enterprise</CardTitle>
                <CardDescription>For accounting firms and scale-ups</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-baseline gap-2">
                  <span className="text-4xl font-bold">$149</span>
                  <span className="text-sm font-semibold text-muted-foreground">/mo</span>
                </div>
                <ul className="space-y-3 text-sm text-muted-foreground">
                  <li className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-green-600" />
                    Unlimited companies
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-green-600" />
                    Unlimited users
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-green-600" />
                    Everything in Professional
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-green-600" />
                    API access
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-green-600" />
                    Priority support
                  </li>
                </ul>
              </CardContent>
              <CardFooter>
                <Button variant="outline" className="w-full" asChild>
                  <Link href="/contact">Contact Sales</Link>
                </Button>
              </CardFooter>
            </Card>
          </div>
        </section>

        {/* FAQ */}
        <section id="faq" className="container mx-auto px-4 py-24 sm:px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold tracking-tight">Frequently asked questions</h2>
          </div>

          <div className="max-w-3xl mx-auto space-y-4">
            {faqs.map((faq) => (
              <Card key={faq.q}>
                <CardHeader className="flex flex-row items-center justify-between py-4">
                  <CardTitle className="text-sm font-medium">{faq.q}</CardTitle>
                  <ChevronRight className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground leading-relaxed">{faq.a}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        {/* CTA */}
        <section className="container mx-auto px-4 py-24 sm:px-6">
          <div className="bg-primary text-primary-foreground rounded-xl p-8 md:p-12 flex flex-col md:flex-row items-center justify-between gap-6">
            <div>
              <h2 className="text-2xl font-bold">Ready to organize your books?</h2>
              <p className="mt-2 text-primary-foreground/90">
                Start your 14-day free trial. No credit card required.
              </p>
            </div>
            <Button size="lg" className="bg-white text-primary hover:bg-primary/90" asChild>
              <Link href="/pricing">Get Started</Link>
            </Button>
          </div>
        </section>
      </main>

      <footer className="border-t py-12">
        <div className="container mx-auto px-4 flex flex-col lg:flex-row justify-between items-center gap-4 text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <span className="font-semibold">GrandLedger</span>
          </div>
          <nav className="flex gap-6">
            {navLinks.map((link) => (
              <Link
                key={link.name}
                href={link.href}
                className="hover:text-foreground transition-colors"
              >
                {link.name}
              </Link>
            ))}
            <Link href="/login">Log in</Link>
          </nav>
          <p>&copy; {new Date().getFullYear()} GrandLedger. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}

function Badge({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors border ${className}`}>
      {children}
    </span>
  )
}
