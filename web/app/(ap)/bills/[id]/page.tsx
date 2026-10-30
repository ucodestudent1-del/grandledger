import dynamic from "next/dynamic"

const BillForm = dynamic(() => import("@/components/BillForm"), { ssr: true })

export async function generateStaticParams() {
  return [{ id: "placeholder" }]
}

export default async function BillDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  return (
    <div>
      <BillForm billId={id} />
    </div>
  )
}
