"use client"

import type React from "react"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useAuthStore } from "@/store/auth-store"
import { Loader2 } from "lucide-react"
import api from "@/lib/api"
import type { User, StandardResponse } from "@/types/auth"

interface ProtectedRouteProps {
  children: React.ReactNode
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const [isLoading, setIsLoading] = useState(true)
  const [isVerifying, setIsVerifying] = useState(false)
  const { isAuthenticated, token, user, _hasHydrated, setAuth, clearAuth, isTokenValid } = useAuthStore()
  const router = useRouter()

  useEffect(() => {
    const verifyAuth = async () => {
      // Zustand hydration이 완료되지 않은 경우 대기
      if (!_hasHydrated) {
        return
      }

      // 토큰이 없거나 만료된 경우 로그인 페이지로 이동
      if (!token || !isTokenValid()) {
        console.log("토큰이 없거나 만료됨, 로그인 페이지로 이동")
        clearAuth() // 만료된 토큰 정리
        setIsLoading(false)
        router.push("/auth/login")
        return
      }

      // 이미 인증 상태이고 사용자 정보가 있으면 검증 없이 통과
      if (isAuthenticated && user) {
        setIsLoading(false)
        return
      }

      // 토큰은 유효하지만 사용자 정보가 없거나 인증 상태가 아닌 경우 서버에서 검증
      try {
        setIsVerifying(true)
        const response = await api.get<StandardResponse<User>>("/auth/me")
        if (response.data.success && response.data.data) {
          setAuth(response.data.data, token)
        } else {
          throw new Error("사용자 정보를 가져올 수 없습니다.")
        }
      } catch (error) {
        console.error("인증 검증 실패:", error)
        clearAuth()
        router.push("/auth/login")
      } finally {
        setIsVerifying(false)
        setIsLoading(false)
      }
    }

    verifyAuth()
  }, [_hasHydrated, token, isAuthenticated, user, setAuth, clearAuth, router, isTokenValid])

  // Zustand hydration이 완료되지 않았거나 로딩 중인 경우
  if (!_hasHydrated || isLoading || isVerifying) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-500" />
          <p className="text-gray-600 dark:text-gray-400">
            {!_hasHydrated ? "시스템 초기화 중..." : isVerifying ? "인증 확인 중..." : "로딩 중..."}
          </p>
        </div>
      </div>
    )
  }

  // 인증되지 않은 경우 (토큰이 없거나 유효하지 않음)
  if (!isAuthenticated || !token || !isTokenValid()) {
    return null // 이미 라우터에서 리다이렉트 처리됨
  }

  return <>{children}</>
}
