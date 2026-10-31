import type { ReactNode } from "react"
import { Inter } from "next/font/google"
import { ThemeProvider } from "@/components/ThemeProvider"
import { ErrorBoundary } from "@/components/ErrorBoundary"
import Providers from "@/app/providers"
import ClientProviders from "@/app/ClientProviders"
import "@/styles/globals.css"

const inter = Inter({ subsets: ["latin"] })

export const metadata = {
  title: "GrandLedger",
  description: "Bookkeeping made simple",
}

export default function RootLayout({
  children,
}: {
  children: ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ErrorBoundary>
          <Providers>
            <ThemeProvider>
              <ClientProviders>{children}</ClientProviders>
            </ThemeProvider>
          </Providers>
        </ErrorBoundary>
      </body>
    </html>
  )
}
