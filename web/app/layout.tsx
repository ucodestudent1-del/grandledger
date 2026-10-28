"use client"

import { Inter } from "next/font/google"
import { usePathname } from "next/navigation"
import { ThemeProvider } from "@/components/ThemeProvider"
import { useAuth } from "@/app/hooks/useAuth"
import Providers from "@/app/providers"
import Sidebar from "@/components/Sidebar"
import Header from "@/components/Header"
import "@/styles/globals.css"

const inter = Inter({ subsets: ["latin"] })

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()
  const { isAuthenticated } = useAuth()

  const isAuthPage = pathname.startsWith("/login") || pathname.startsWith("/signup")

  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>
          <ThemeProvider>
            {isAuthenticated && !isAuthPage ? (
              <div className="flex h-screen overflow-hidden">
                <Sidebar />
                <div className="flex-1 flex flex-col overflow-hidden">
                  <Header />
                  <main className="flex-1 overflow-y-auto bg-background p-6">
                    {children}
                  </main>
                </div>
              </div>
            ) : (
              children
            )}
          </ThemeProvider>
        </Providers>
      </body>
    </html>
  )
}