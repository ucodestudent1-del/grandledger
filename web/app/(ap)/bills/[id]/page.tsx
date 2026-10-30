import BillDetailView from "./BillDetailView"

export async function generateStaticParams() {
  return [{ id: "placeholder" }]
}

export default function BillDetailPage() {
  return <BillDetailView />
}
