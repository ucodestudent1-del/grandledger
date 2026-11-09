"use client"

import Link from "next/link"
import {
  ArrowRight,
  Check,
  Clock,
  CreditCard,
  FileText,
  Hash,
  Receipt,
  RefreshCw,
  Shield,
  Zap,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"

const features = [
  { title: "Immutable double-entry ledger", icon: Hash },
  { title: "Professional invoices (AR)", icon: Receipt },
  { title: "Vendor bills (AP)", icon: CreditCard },
  { title: "Bank reconciliation", icon: RefreshCw },
  { title: "Audit-ready reports", icon: FileText },
  { title: "Multi-client security", icon: Shield },
]

const plans = [
  {
    name: "Starter",
    description: "For freelancers and solo business owners",
    price: 19,
    priceId: "price_starter_monthly",
    popular: false,
    limits: ["1 company", "3 users", "Invoicing & payments", "Financial reports"],
    limitsPlus: ["Bank reconciliation", "Multi-client access"],
    cta: "Start Free Trial",
    ctaHref: "/signup?plan=starter",
  },
  {
    name: "Professional",
    description: "For growing businesses and bookkeepers",
    price: 49,
    priceId: "price_professional_monthly",
    popular: true,
    limits: ["5 companies", "10 users", "Invoicing & payments", "Bank reconciliation", "Financial reports", "Accountant access"],
    limitsPlus: [],
    cta: "Start Free Trial",
    ctaHref: "/signup?plan=professional",
  },
  {
    name: "Enterprise",
    description: "For accounting firms and scale-ups",
    price: 149,
    priceId: "price_enterprise_monthly",
    popular: false,
    limits: ["Unlimited companies", "Unlimited users", "API access", "Priority support", "Everything in Professional"],
    limitsPlus: [],
    cta: "Contact Sales",
    ctaHref: "/contact",
  },
]

export default function PricingPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="container mx-auto flex h-16 items-center justify-between px-4">
        <Link href="/" className="text-2xl font-bold tracking-tight">
          GrandLedger
        </Link>
        <nav className="flex items-center gap-6">
          <Link href="/landing#features" className="text-sm text-muted-foreground hover:text-foreground">
            Features
          </Link>
          <Link href="/landing#faq" className="text-sm text-muted-foreground hover:text-foreground">
            FAQ
          </Link>
          <Link href="/login" className="text-sm text-muted-foreground hover:text-foreground">
            Log in
          </Link>
          <Button asChild>
            <Link href="/signup">Get Started</Link>
          </Button>
        </nav>
      </header>

      <main className="flex-1">
        <section className="container mx-auto px-4 py-20 sm:px-6">
          <div className="text-center mb-16">
            <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-green-200 bg-green-50 text-green-700 text-xs font-semibold">
              <ArrowRight className="h-3 w-3 mr-1" />
              14-day free trial — no credit card required
            </span>
            <h1 className="mt-6 text-3xl font-bold tracking-tight sm:text-4xl">
              Simple, transparent pricing
            </h1>
            <p className="mt-4 text-lg text-muted-foreground max-w-2xl mx-auto">
              Choose the plan that fits your business. Upgrade or cancel anytime.
            </p>
          </div>

          <div className="grid gap-8 sm:grid-cols-3 max-w-6xl mx-auto">
            {plans.map((plan) => (
              <Card key={plan.name} className={plan.popular ? "relative border-primary bg-primary/5" : "p-8"}>
                {plan.popular && (
                  <Badge className="absolute top-0 right-0 mt-4 mr-4 bg-primary text-primary-foreground px-3 py-1 rounded-full text-xs font-semibold">
                    Most Popular
                  </Badge>
                )}
                <CardHeader>
                  <CardTitle>{plan.name}</CardTitle>
                  <CardDescription>{plan.description}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="flex items-baseline gap-2">
                    <span className="text-4xl font-bold">${plan.price}</span>
                    <span className="text-sm font-semibold text-muted-foreground">/mo</span>
                  </div>
                  <ul className="space-y-3 text-sm text-muted-foreground">
                    {plan.limits.map((limit) => (
                      <li key={limit} className="flex items-center gap-2">
                        <Check className="h-4 w-4 text-green-600" />
                        {limit}
                      </li>
                    ))}
                  </ul>
                </CardContent>
                <CardFooter>
                  <Button className="w-full" asChild>
                    <Link href={plan.ctaHref}>{plan.cta}</Link>
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </div>

          <div className="mt-16 border-t pt-12">
            <h3 className="text-center text-2xl font-bold mb-8">Compare features</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="pb-4 font-medium text-muted-foreground"></th>
                    {plans.map((p) => (
                      <th key={p.name} className="pb-4 text-center font-medium text-muted-foreground">
                        {p.name}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {features.map((feature) => (
                    <tr key={feature.title} className="border-b">
                      <td className="py-4 font-medium">{feature.title}</td>
                      {plans.map((p) => (
                        <td key={p.name} className="py-4 text-center">
                          {p.limits.includes(feature.title) || p.limitsPlus.includes(feature.title) || p.name === "Enterprise" ? (
                            <Check className="h-4 w-4 text-green-600 mx-auto" />
                          ) : (
                            <span className="h-4 w-4 mx-auto text-muted-foreground">—</span>
                          )}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="mt-16 text-center">
            <h3 className="text-2xl font-bold">Need something custom?</h3>
            <p className="mt-2 text-muted-foreground max-w-2xl mx-auto">
              Need more users, custom integrations, or dedicated support? We offer
              enterprise plans with SLA-backed support.
            </p>
            <Button asChild>
              <Link href="/contact">Contact Sales</Link>
            </Button>
          </div>
        </section>
      </main>

      <footer className="border-t py-12">
        <div className="container mx-auto px-4 flex flex-col lg:flex-row justify-between items-center gap-4 text-sm text-muted-foreground">
          <span className="font-semibold">GrandLedger</span>
          <nav className="flex gap-6">
            <Link href="/landing#features" className="hover:text-foreground transition-colors">
              Features
            </Link>
            <Link href="/landing#faq" className="hover:text-foreground transition-colors">
              FAQ
            </Link>
            <Link href="/login" className="hover:text-foreground transition-colors">
              Log in
            </Link>
          </nav>
          <p>&copy; {new Date().getFullYear()} GrandLedger. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}
