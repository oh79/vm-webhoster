"use client"

import { ProtectedRoute } from "@/components/auth/protected-route"
import { DashboardSidebar } from "@/components/dashboard/sidebar"
import { DashboardHeader } from "@/components/dashboard/header"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <DashboardSidebar />
        <div className="lg:pl-64">
          <DashboardHeader />
          <main className="py-6 px-6">
            {children}
          </main>
        </div>
      </div>
    </ProtectedRoute>
  )
}
