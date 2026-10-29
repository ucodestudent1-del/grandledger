// TypeScript type definitions for API responses

export interface Company {
  id: string
  name: string
  slug: string
  currency: string
  financial_year_start?: string
  created_at: string
  updated_at: string
}

export interface User {
  id: string
  company_id: string
  email: string
  name: string
  role: string
  is_external_accountant: boolean
  created_at: string
}

export interface Account {
  id: string
  company_id: string
  code: string
  name: string
  type: "asset" | "liability" | "equity" | "revenue" | "expense"
  parent_id?: string
  is_active: boolean
  is_system: boolean
  created_at: string
}

export interface Contact {
  id: string
  company_id: string
  name: string
  type: "customer" | "vendor"
  email?: string
  phone?: string
  address?: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface JournalLine {
  id: string
  journal_entry_id: string
  account_id: string
  description?: string
  debit: string
  credit: string
  created_at: string
}

export interface JournalEntry {
  id: string
  company_id: string
  number: string
  entry_date: string
  description?: string
  status: "draft" | "posted" | "void"
  posted_at?: string
  posted_by?: string
  source?: string
  created_by: string
  lines: JournalLine[]
  created_at: string
  updated_at: string
}

export interface InvoiceLine {
  id: string
  invoice_id: string
  description: string
  qty: string
  unit_price: string
  tax_rate: string
  amount: string
  account_id?: string
}

export interface Invoice {
  id: string
  company_id: string
  contact_id: string
  number: string
  status: "draft" | "issued" | "void" | "paid"
  issue_date?: string
  due_date?: string
  subtotal: string
  tax_total: string
  total: string
  currency: string
  created_at: string
  updated_at: string
  lines: InvoiceLine[]
}

export interface Payment {
  id: string
  company_id: string
  contact_id: string
  type: "payment" | "receipt"
  amount: string
  payment_date: string
  allocated_to?: Record<string, unknown>[]
  journal_entry_id?: string
  reference?: string
  created_at: string
}

export interface BillLine {
  id: string
  bill_id: string
  description: string
  qty: string
  unit_price: string
  tax_rate: string
  amount: string
  account_id?: string
}

export interface Bill {
  id: string
  company_id: string
  contact_id: string
  number: string
  status: "draft" | "posted" | "void"
  issue_date?: string
  due_date?: string
  subtotal: string
  tax_total: string
  total: string
  currency: string
  created_at: string
  updated_at: string
  lines: BillLine[]
}

export interface BankAccount {
  id: string
  company_id: string
  name: string
  bank_name?: string
  account_number?: string
  starting_balance: string
  currency: string
  created_at: string
  updated_at: string
}

export interface BankTransaction {
  id: string
  company_id: string
  bank_account_id: string
  date: string
  description: string
  amount: string
  balance?: string
  imported_at: string
  matched: boolean
  journal_entry_id?: string
  status: "pending" | "cleared" | "reconciled"
}

export interface AuditLog {
  id: string
  company_id: string
  user_id?: string
  action: string
  entity_type: string
  entity_id?: string
  before?: Record<string, unknown>
  after?: Record<string, unknown>
  ip_address?: string
  created_at: string
}

export interface ReportResponse {
  report: string
  period?: {
    start_date: string
    end_date: string
  }
  as_of?: string
}

export interface ProfitLossResponse {
  report: "profit-loss"
  period: { start_date: string; end_date: string }
  revenue: { total: string; items: { account_name: string; amount: string }[] }
  expense: { total: string; items: { account_name: string; amount: string }[] }
  net_income: string
}

export interface BalanceSheetResponse {
  report: "balance-sheet"
  as_of: string
  assets: { total: string; items: { account_name: string; amount: string }[] }
  liabilities: { total: string; items: { account_name: string; amount: string }[] }
  equity: { total: string; items: { account_name: string; amount: string }[] }
}

export interface TrialBalanceResponse {
  report: "trial-balance"
  as_of: string
  accounts: { code: string; name: string; debit: string; credit: string; balance: string }[]
}

export interface GeneralLedgerEntry {
  date: string
  number: string
  description: string
  debit: string
  credit: string
  balance: string
}

export interface GeneralLedgerResponse {
  report: "general-ledger"
  as_of: string
  account: { id: string; code: string; name: string; type: string }
  entries: GeneralLedgerEntry[]
}

export interface AgingBucket {
  current: string
  days_1_30?: string
  days_31_60?: string
  days_61_90?: string
  days_91_plus?: string
  total: string
}

export interface ArAgingContact {
  contact_name: string
  total_due: string
  buckets: AgingBucket
}

export interface ArAgingResponse {
  report: "ar-aging"
  as_of: string
  contacts: ArAgingContact[]
}

export interface ApAgingResponse {
  report: "ap-aging"
  as_of: string
  vendors: { vendor_name: string; total_due: string; buckets: AgingBucket }[]
}

export interface JournalEntryCreate {
  entry_date: string
  description: string
  lines: { account_id: string; description?: string; debit?: string; credit?: string }[]
}

export interface JournalEntryList {
  items: JournalEntry[]
  pagination: {
    page: number
    page_size: number
    total: number
    total_pages: number
  }
}

export interface ContactList {
  items: Contact[]
  pagination: {
    page: number
    page_size: number
    total: number
    total_pages: number
  }
}

export interface AuditList {
  items: AuditLog[]
  pagination: {
    page: number
    page_size: number
    total: number
    total_pages: number
  }
}

declare global {
  interface Window {
    google: {
      accounts: {
        id: {
          initialize: (config: { client_id: string; callback: (response: { credential: string }) => void }) => void
          renderButton: (element: HTMLElement | null, options: Record<string, unknown>) => void
        }
      }
    }
  }
}
