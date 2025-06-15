import { create } from "zustand"
import { persist } from "zustand/middleware"
import type { User } from "@/types/auth"

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  _hasHydrated: boolean
  setAuth: (user: User, token: string) => void
  clearAuth: () => void
  setHasHydrated: (hasHydrated: boolean) => void
  isTokenValid: () => boolean
}

// JWT 토큰 디코딩 함수 (간단한 구현)
const isTokenExpired = (token: string): boolean => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    const currentTime = Date.now() / 1000
    return payload.exp < currentTime
  } catch (error) {
    return true // 토큰 파싱 실패 시 만료로 간주
  }
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      _hasHydrated: false,
      setAuth: (user, token) => set({ user, token, isAuthenticated: true }),
      clearAuth: () => set({ user: null, token: null, isAuthenticated: false }),
      setHasHydrated: (hasHydrated) => {
        set({ _hasHydrated: hasHydrated })
        
        // hydration 완료 후 토큰 유효성 확인
        if (hasHydrated) {
          const { token, user } = get()
          if (token && user) {
            // 토큰이 만료되었다면 인증 상태 정리
            if (isTokenExpired(token)) {
              set({ user: null, token: null, isAuthenticated: false })
            } else {
              set({ isAuthenticated: true })
            }
          }
        }
      },
      isTokenValid: () => {
        const { token } = get()
        if (!token) return false
        return !isTokenExpired(token)
      },
    }),
    {
      name: "auth-storage",
      onRehydrateStorage: () => (state) => {
        // persist 미들웨어 hydration 완료 시 상태 업데이트
        state?.setHasHydrated(true)
      },
    },
  ),
)
