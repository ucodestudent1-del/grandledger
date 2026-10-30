import VendorDetailView from "./VendorDetailView"

export async function generateStaticParams() {
  return [{ id: "placeholder" }]
}

export default function VendorDetailPage() {
  return <VendorDetailView />
}
