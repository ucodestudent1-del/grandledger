import JournalDetailView from "./JournalDetailView"

export async function generateStaticParams() {
  return [{ id: "placeholder" }]
}

export default function JournalDetailPage() {
  return <JournalDetailView />
}
