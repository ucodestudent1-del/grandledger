import InvoiceDetailView from "./InvoiceDetailView"

export async function generateStaticParams() {
  return [{ id: "placeholder" }]
}

export default function InvoiceDetailPage() {
  return <InvoiceDetailView />
}
