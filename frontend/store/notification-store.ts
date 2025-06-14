import { create } from "zustand"
import type { Notification } from "@/types/notification"

interface NotificationState {
  notifications: Notification[]
  unreadCount: number
  addNotification: (notification: Notification) => void
  markAsRead: (id: string) => void
  markAllAsRead: () => void
  removeNotification: (id: string) => void
  clearAll: () => void
}

export const useNotificationStore = create<NotificationState>((set) => ({
  notifications: [],
  unreadCount: 0,
  addNotification: (notification) =>
    set((state) => ({
      notifications: [notification, ...state.notifications],
      unreadCount: state.unreadCount + 1,
    })),
  markAsRead: (id) =>
    set((state) => {
      const updatedNotifications = state.notifications.map((notification) =>
        notification.id === id ? { ...notification, read: true } : notification,
      )
      const unreadCount = updatedNotifications.filter((notification) => !notification.read).length
      return { notifications: updatedNotifications, unreadCount }
    }),
  markAllAsRead: () =>
    set((state) => ({
      notifications: state.notifications.map((notification) => ({ ...notification, read: true })),
      unreadCount: 0,
    })),
  removeNotification: (id) =>
    set((state) => {
      const notification = state.notifications.find((n) => n.id === id)
      const unreadCount = notification && !notification.read ? state.unreadCount - 1 : state.unreadCount
      return {
        notifications: state.notifications.filter((notification) => notification.id !== id),
        unreadCount,
      }
    }),
  clearAll: () => set({ notifications: [], unreadCount: 0 }),
}))
