"use client"

import { useAuthStore } from "@/store/auth-store"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { ModeToggle } from "@/components/mode-toggle"
import { NotificationCenter } from "@/components/dashboard/notification-center"
import { MobileNav } from "@/components/dashboard/mobile-nav"
import { useIsMobile } from "@/hooks/use-mobile"

export function DashboardHeader() {
  const { user } = useAuthStore()
  const isMobile = useIsMobile()

  return (
    <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 h-16 flex items-center justify-between px-6">
      <div className="flex items-center">
        {isMobile && <MobileNav />}
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white lg:ml-0 ml-4">
          환영합니다, {user?.username}님!
        </h2>
      </div>

      <div className="flex items-center gap-4">
        <NotificationCenter />
        <ModeToggle />
        <div className="flex items-center gap-3">
          <div className="text-right hidden sm:block">
            <p className="text-sm font-medium text-gray-900 dark:text-white">{user?.username}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">{user?.email}</p>
          </div>
          <Avatar>
            <AvatarFallback>{user?.username?.charAt(0).toUpperCase() || "U"}</AvatarFallback>
          </Avatar>
        </div>
      </div>
    </header>
  )
}
