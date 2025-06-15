"use client"

import { useEffect, useRef } from "react"
import { useHostingStore } from "@/store/hosting-store"
import { useNotificationStore } from "@/store/notification-store"
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
  const { addNotification } = useNotificationStore()
  const { showSuccess, showError } = useToast()
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null)

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
        showSuccess("호스팅 생성이 시작되었습니다! 완료까지 1-2분 정도 소요됩니다.")
        
        // 알림 센터에도 알림 추가
        addNotification({
          id: `hosting-create-${Date.now()}`,
          title: "호스팅 생성 시작",
          message: "새로운 호스팅 인스턴스 생성이 시작되었습니다. 완료까지 1-2분 정도 소요됩니다.",
          type: "info",
          read: false,
          createdAt: new Date().toISOString(),
        })
        
        // 생성 중인 경우 빠른 폴링 시작 (5초마다)
        startFastPolling()
        
        return response.data
      }
    } catch (error: any) {
      const message = error.response?.data?.detail || error.response?.data?.message || "호스팅 인스턴스 생성에 실패했습니다"
      showError(message)
      
      // 실패 알림도 추가
      addNotification({
        id: `hosting-error-${Date.now()}`,
        title: "호스팅 생성 실패",
        message: message,
        type: "error",
        read: false,
        createdAt: new Date().toISOString(),
      })
      
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
        stopPolling() // 폴링 중지
        
        // 삭제 완료 알림 추가
        addNotification({
          id: `hosting-delete-${Date.now()}`,
          title: "호스팅 삭제 완료",
          message: "호스팅 인스턴스가 성공적으로 삭제되었습니다.",
          type: "success",
          read: false,
          createdAt: new Date().toISOString(),
        })
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
        const newInstance = response.data
        const currentInstance = instances[0]
        
        // 상태가 변경된 경우 알림 표시
        if (currentInstance && currentInstance.status !== newInstance.status) {
          if (newInstance.status === "running") {
            showSuccess("🎉 호스팅이 성공적으로 생성되었습니다!")
            stopPolling() // 생성 완료 시 빠른 폴링 중지
            
            // 성공 알림 추가
            addNotification({
              id: `hosting-success-${Date.now()}`,
              title: "🎉 호스팅 생성 완료",
              message: `VM-${newInstance.vm_id} 호스팅이 성공적으로 생성되어 사용할 수 있습니다!`,
              type: "success",
              read: false,
              createdAt: new Date().toISOString(),
            })
          } else if (newInstance.status === "error") {
            showError("호스팅 생성 중 오류가 발생했습니다.")
            stopPolling()
            
            // 오류 알림 추가
            addNotification({
              id: `hosting-error-${Date.now()}`,
              title: "호스팅 생성 오류",
              message: "호스팅 생성 중 오류가 발생했습니다. 다시 시도해주세요.",
              type: "error",
              read: false,
              createdAt: new Date().toISOString(),
            })
          }
        }
        
        setInstances([newInstance])
      }
    } catch (error: any) {
      console.error("Failed to refresh instance status:", error)
      // 404는 호스팅이 삭제되었다는 의미
      if (error.response?.status === 404) {
        setInstances([])
        stopPolling()
      }
    }
  }

  const startFastPolling = () => {
    stopPolling() // 기존 폴링 중지
    pollingIntervalRef.current = setInterval(() => {
      refreshInstanceStatus()
    }, 5000) // 5초마다 폴링
  }

  const stopPolling = () => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current)
      pollingIntervalRef.current = null
    }
  }

  useEffect(() => {
    fetchInstances()
    
    // 컴포넌트 언마운트 시 폴링 정리
    return () => {
      stopPolling()
    }
  }, [])

  // 상태 기반 폴링 관리
  useEffect(() => {
    if (instances.length > 0) {
      const activeInstance = instances[0]
      
      if (activeInstance.status === "creating" || activeInstance.status === "stopping") {
        // 생성/중지 중인 경우 빠른 폴링 시작
        startFastPolling()
      } else {
        // 안정 상태인 경우 폴링 중지
        stopPolling()
      }
    } else {
      stopPolling()
    }
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
