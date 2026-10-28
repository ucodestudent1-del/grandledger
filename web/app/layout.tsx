import { Inter } from "next/font/google"
import { ThemeProvider } from "@/components/ThemeProvider"
import Providers from "@/app/providers"
import "@/styles/globals.css"

const inter = Inter({ subsets: ["latin"] })

export const metadata = {
  title: "GrandLedger — Bookkeeping SaaS",
  description: "Multi-tenant double-entry bookkeeping for freelancers and small businesses",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>
          <ThemeProvider>
            {children}
          </ThemeProvider>
        </Providers>
      </body>
    </html>
  )
}
