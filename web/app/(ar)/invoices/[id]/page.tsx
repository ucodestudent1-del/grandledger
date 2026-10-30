import dynamic from "next/dynamic"

const InvoiceForm = dynamic(() => import("@/components/InvoiceForm"), { ssr: true })

export async function generateStaticParams() {
  return [{ id: "placeholder" }]
}

export default async function InvoiceDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  return <InvoiceForm invoiceId={id} />
}
