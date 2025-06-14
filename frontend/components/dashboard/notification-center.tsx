"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Bell, Check, Info, AlertCircle, CheckCircle, XCircle, Trash2 } from "lucide-react"
import { useNotificationStore } from "@/store/notification-store"
import { cn } from "@/lib/utils"
import type { Notification } from "@/types/notification"

export function NotificationCenter() {
  const [open, setOpen] = useState(false)
  const { notifications, unreadCount, markAsRead, markAllAsRead, removeNotification, clearAll } = useNotificationStore()

  // Mock notifications for demo
  useEffect(() => {
    const mockNotifications: Notification[] = [
      {
        id: "1",
        title: "호스팅 생성 완료",
        message: "새로운 호스팅 인스턴스가 성공적으로 생성되었습니다.",
        type: "success",
        read: false,
        createdAt: new Date(Date.now() - 1000 * 60 * 5).toISOString(), // 5분 전
      },
      {
        id: "2",
        title: "높은 CPU 사용량",
        message: "인스턴스의 CPU 사용량이 높습니다 (85%).",
        type: "warning",
        read: false,
        createdAt: new Date(Date.now() - 1000 * 60 * 30).toISOString(), // 30분 전
      },
      {
        id: "3",
        title: "시스템 점검 예정",
        message: "내일 오전 2시(UTC)에 시스템 점검이 예정되어 있습니다.",
        type: "info",
        read: true,
        createdAt: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(), // 2시간 전
      },
      {
        id: "4",
        title: "결제 정보 업데이트",
        message: "이번 달 청구서가 생성되었습니다.",
        type: "info",
        read: true,
        createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(), // 1일 전
      },
    ]

    // Add mock notifications to the store
    mockNotifications.forEach((notification) => {
      if (!notifications.some((n) => n.id === notification.id)) {
        useNotificationStore.getState().addNotification(notification)
      }
    })
  }, [])

  const handleMarkAsRead = (id: string) => {
    markAsRead(id)
  }

  const handleRemove = (id: string) => {
    removeNotification(id)
  }

  const getIcon = (type: string) => {
    switch (type) {
      case "info":
        return <Info className="h-4 w-4 text-blue-500" />
      case "success":
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case "warning":
        return <AlertCircle className="h-4 w-4 text-yellow-500" />
      case "error":
        return <XCircle className="h-4 w-4 text-red-500" />
      default:
        return <Info className="h-4 w-4" />
    }
  }

  const formatTime = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMins / 60)
    const diffDays = Math.floor(diffHours / 24)

    if (diffMins < 1) return "방금 전"
    if (diffMins < 60) return `${diffMins}분 전`
    if (diffHours < 24) return `${diffHours}시간 전`
    if (diffDays < 7) return `${diffDays}일 전`
    return date.toLocaleDateString()
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button variant="outline" size="icon" className="relative">
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs text-white">
              {unreadCount > 9 ? "9+" : unreadCount}
            </span>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80 p-0" align="end">
        <div className="flex items-center justify-between p-4 border-b">
          <h3 className="font-medium">알림</h3>
          <div className="flex gap-2">
            {unreadCount > 0 && (
              <Button variant="ghost" size="sm" onClick={markAllAsRead} className="h-8 px-2 text-xs">
                <Check className="h-3.5 w-3.5 mr-1" />
                모두 읽음
              </Button>
            )}
            <Button variant="ghost" size="sm" onClick={clearAll} className="h-8 px-2 text-xs">
              <Trash2 className="h-3.5 w-3.5 mr-1" />
              모두 삭제
            </Button>
          </div>
        </div>
        {notifications.length === 0 ? (
          <div className="p-4 text-center text-sm text-gray-500">알림이 없습니다</div>
        ) : (
          <ScrollArea className="h-[300px]">
            <div className="divide-y">
              {notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={cn(
                    "p-4 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors",
                    !notification.read && "bg-blue-50 dark:bg-blue-900/20",
                  )}
                >
                  <div className="flex gap-3">
                    <div className="mt-0.5">{getIcon(notification.type)}</div>
                    <div className="flex-1 space-y-1">
                      <div className="flex items-start justify-between gap-2">
                        <p className="text-sm font-medium">{notification.title}</p>
                        <span className="text-xs text-gray-500">{formatTime(notification.createdAt)}</span>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">{notification.message}</p>
                      <div className="flex gap-2 pt-1">
                        {!notification.read && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleMarkAsRead(notification.id)}
                            className="h-7 px-2 text-xs"
                          >
                            읽음 표시
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRemove(notification.id)}
                          className="h-7 px-2 text-xs text-red-600 hover:text-red-700 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
                        >
                          삭제
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        )}
      </PopoverContent>
    </Popover>
  )
}
