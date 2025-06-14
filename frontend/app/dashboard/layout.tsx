"use client"

import type React from "react"

import { ProtectedRoute } from "@/components/auth/protected-route"
import { DashboardSidebar } from "@/components/dashboard/sidebar"
import { DashboardHeader } from "@/components/dashboard/header"
import { useIsMobile } from "@/hooks/use-mobile"
import { ErrorBoundary } from "@/components/error-boundary"
import { useRealtimeStatus } from "@/hooks/use-realtime-status"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const isMobile = useIsMobile()

  // Initialize real-time status updates
  useRealtimeStatus()

  return (
    <ProtectedRoute>
      <ErrorBoundary>
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
          {!isMobile && <DashboardSidebar />}
          <div className={isMobile ? "" : "lg:pl-64"}>
            <DashboardHeader />
            <main className="p-4 md:p-6">{children}</main>
          </div>
        </div>
      </ErrorBoundary>
    </ProtectedRoute>
  )
}
