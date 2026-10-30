import dynamic from "next/dynamic"

const ContactForm = dynamic(() => import("@/components/ContactForm"), { ssr: true })

export async function generateStaticParams() {
  return [{ id: "placeholder" }]
}

export default async function CustomerDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  return <ContactForm contactType="customer" contactId={id} />
}
