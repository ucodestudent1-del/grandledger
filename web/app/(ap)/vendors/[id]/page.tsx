import dynamic from "next/dynamic"

const VendorForm = dynamic(() => import("@/components/VendorForm"), { ssr: true })

export async function generateStaticParams() {
  return [{ id: "placeholder" }]
}

export default async function VendorDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  return <VendorForm vendorId={id} />
}
