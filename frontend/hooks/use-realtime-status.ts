"use client"

import { useEffect, useRef } from "react"
import { useHostingStore } from "@/store/hosting-store"
import { hostingApi } from "@/lib/hosting"

export function useRealtimeStatus() {
  const { instances, updateInstance } = useHostingStore()
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    const pollStatus = async () => {
      const activeInstances = instances.filter(
        (instance) => instance.status === "creating" || instance.status === "stopping",
      )

      for (const instance of activeInstances) {
        try {
          const { instance: updatedInstance } = await hostingApi.getById(instance.id)
          if (updatedInstance.status !== instance.status) {
            updateInstance(instance.id, { status: updatedInstance.status })
          }
        } catch (error) {
          console.error(`Failed to update status for instance ${instance.id}:`, error)
        }
      }
    }

    // Poll every 10 seconds for active instances
    if (instances.some((instance) => instance.status === "creating" || instance.status === "stopping")) {
      intervalRef.current = setInterval(pollStatus, 10000)
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [instances, updateInstance])

  // Handle visibility change - refresh when tab becomes visible
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        // Refresh all instances when tab becomes visible
        instances.forEach(async (instance) => {
          try {
            const { instance: updatedInstance } = await hostingApi.getById(instance.id)
            updateInstance(instance.id, updatedInstance)
          } catch (error) {
            console.error(`Failed to refresh instance ${instance.id}:`, error)
          }
        })
      }
    }

    document.addEventListener("visibilitychange", handleVisibilityChange)
    return () => document.removeEventListener("visibilitychange", handleVisibilityChange)
  }, [instances, updateInstance])
}
