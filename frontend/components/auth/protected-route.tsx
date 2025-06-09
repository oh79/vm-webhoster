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
  const { isAuthenticated, token, setAuth, clearAuth } = useAuthStore()
  const router = useRouter()

  useEffect(() => {
    const verifyAuth = async () => {
      if (!token) {
        router.push("/auth/login")
        return
      }

      try {
        const response = await api.get<StandardResponse<User>>("/auth/me")
        if (response.data.success && response.data.data) {
          setAuth(response.data.data, token)
        } else {
          throw new Error("사용자 정보를 가져올 수 없습니다.")
        }
      } catch (error) {
        clearAuth()
        router.push("/auth/login")
      } finally {
        setIsLoading(false)
      }
    }

    verifyAuth()
  }, [token, setAuth, clearAuth, router])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  return <>{children}</>
}
