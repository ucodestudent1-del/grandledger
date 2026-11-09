"use client"

import { Invoice } from "@/types/api"

export function EmptyInvoices() {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <svg
        className="w-16 h-16 text-muted-foreground mb-4"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1}
          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v16a2 2 0 01-2 2H7a2 2 0 01-2-2z"
        />
      </svg>
      <h3 className="text-lg font-semibold mb-2">No invoices yet</h3>
      <p className="text-muted-foreground mb-6 max-w-xs">
        Create your first invoice to get started. Invoices help you track
        revenue and manage customer payments.
      </p>
      <button className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90">
        Create Invoice
      </button>
    </div>
  )
}

export function EmptyJournalEntries() {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <svg
        className="w-16 h-16 text-muted-foreground mb-4"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1}
          d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <h3 className="text-lg font-semibold mb-2">No journal entries</h3>
      <p className="text-muted-foreground mb-6 max-w-xs">
        Record your first journal entry to start tracking financial
        transactions.
      </p>
      <button className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90">
        Create Journal Entry
      </button>
    </div>
  )
}

export function EmptyContacts() {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <svg
        className="w-16 h-16 text-muted-foreground mb-4"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1}
          d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20h7m-10 0v-2c0-1.1.5-2.1 1.356-2.857M17 20h7m-10 0v-2c0-1.1-.5-2.1-1.356-2.857M3 13a2 2 0 114 0v1a2 2 0 01-4 0v-1zm12.657-7.857L20 12l-1.343-1.343a8 8 0 11-11.314 0L4 12l1.343 1.343a8 8 0 0111.314 0zM7.5 5.5a3 3 0 11-6 0 3 3 0 016 0z"
        />
      </svg>
      <h3 className="text-lg font-semibold mb-2">No contacts</h3>
      <p className="text-muted-foreground mb-6 max-w-xs">
        Add your first customer or vendor to get started with invoicing and
        bills.
      </p>
      <button className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90">
        Add Contact
      </button>
    </div>
  )
}

export function EmptyReports() {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <svg
        className="w-16 h-16 text-muted-foreground mb-4"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1}
          d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
        />
      </svg>
      <h3 className="text-lg font-semibold mb-2">No report data</h3>
      <p className="text-muted-foreground mb-6 max-w-xs">
        Generate financial reports once you have posted journal entries.
      </p>
    </div>
  )
}
