import CustomerDetailView from "./CustomerDetailView"

export async function generateStaticParams() {
  return [{ id: "placeholder" }]
}

export default function CustomerDetailPage() {
  return <CustomerDetailView />
}
