import dynamic from "next/dynamic"

const JournalForm = dynamic(() => import("@/components/JournalForm"), { ssr: true })

export async function generateStaticParams() {
  return [{ id: "placeholder" }]
}

export default async function JournalDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  return <JournalForm journalId={id} />
}
