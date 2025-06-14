"use client"

import { useEffect } from "react"
import { useHostingStore } from "@/store/hosting-store"
import { useToast } from "@/hooks/use-toast"
import { hostingApi } from "@/lib/hosting"
import type { CreateHostingRequest } from "@/types/hosting"

export function useHosting() {
  const {
    instances,
    isLoading,
    error,
    setInstances,
    addInstance,
    updateInstance,
    removeInstance,
    setLoading,
    setError,
  } = useHostingStore()
  const { showSuccess, showError } = useToast()

  const fetchInstances = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await hostingApi.getAll()
      if (response.success && response.data) {
        // 백엔드에서는 단일 호스팅만 지원하므로 배열로 변환
        setInstances([response.data])
      } else {
        // 호스팅이 없는 경우
        setInstances([])
      }
    } catch (error: any) {
      // 404는 호스팅이 없다는 의미이므로 빈 배열로 설정
      if (error.response?.status === 404) {
        setInstances([])
        setError(null)
      } else {
        const message = error.response?.data?.detail || error.response?.data?.message || "호스팅 인스턴스를 가져오는데 실패했습니다"
        setError(message)
        showError(message)
      }
    } finally {
      setLoading(false)
    }
  }

  const createInstance = async (data: CreateHostingRequest) => {
    setLoading(true)
    try {
      const response = await hostingApi.create(data)
      if (response.success && response.data) {
        addInstance(response.data)
        showSuccess(response.message || "호스팅 인스턴스가 생성되었습니다!")
        return response.data
      }
    } catch (error: any) {
      const message = error.response?.data?.detail || error.response?.data?.message || "호스팅 인스턴스 생성에 실패했습니다"
      showError(message)
      throw error
    } finally {
      setLoading(false)
    }
  }

  const deleteInstance = async () => {
    try {
      const response = await hostingApi.delete()
      if (response.success) {
        setInstances([]) // 모든 인스턴스 제거
        showSuccess(response.message || "호스팅 인스턴스가 삭제되었습니다!")
      }
    } catch (error: any) {
      const message = error.response?.data?.detail || error.response?.data?.message || "호스팅 인스턴스 삭제에 실패했습니다"
      showError(message)
      throw error
    }
  }

  const refreshInstanceStatus = async () => {
    try {
      const response = await hostingApi.getStatus()
      if (response.success && response.data) {
        setInstances([response.data])
      }
    } catch (error: any) {
      console.error("Failed to refresh instance status:", error)
      // 404는 호스팅이 삭제되었다는 의미
      if (error.response?.status === 404) {
        setInstances([])
      }
    }
  }

  useEffect(() => {
    fetchInstances()
  }, [])

  // Poll for status updates every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      if (instances.length > 0) {
        const activeInstance = instances[0]
        if (activeInstance.status === "creating" || activeInstance.status === "stopping") {
          refreshInstanceStatus()
        }
      }
    }, 30000)

    return () => clearInterval(interval)
  }, [instances])

  return {
    instances,
    isLoading,
    error,
    fetchInstances,
    createInstance,
    deleteInstance,
    refreshInstanceStatus,
  }
}
