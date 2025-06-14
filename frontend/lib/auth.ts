import api from "./api"
import type { LoginRequest, RegisterRequest, AuthResponse, User, StandardResponse } from "@/types/auth"
import { useAuthStore } from "@/store/auth-store" // 올바른 경로로 수정

export const authApi = {
  login: async (data: LoginRequest): Promise<AuthResponse> => {
    // FastAPI OAuth2PasswordRequestForm 형식으로 전송
    const formData = new FormData()
    formData.append("username", data.username) // 이메일을 username으로 전송
    formData.append("password", data.password)

    const response = await api.post<StandardResponse<{
      access_token: string
      token_type: string
      expires_in: number
      user: User
    }>>("/auth/login", formData, {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    })
    
    // StandardResponse에서 실제 데이터를 추출하여 AuthResponse 형식으로 변환
    if (response.data.success && response.data.data) {
      return {
        access_token: response.data.data.access_token,
        token_type: response.data.data.token_type,
        user: response.data.data.user
      }
    } else {
      throw new Error(response.data.message || "로그인에 실패했습니다.")
    }
  },

  register: async (data: RegisterRequest): Promise<StandardResponse> => {
    const response = await api.post<StandardResponse>("/auth/register", data)
    return response.data
  },

  me: async (): Promise<StandardResponse<User>> => {
    const response = await api.get<StandardResponse<User>>("/auth/me")
    return response.data
  },

  checkEmail: async (email: string): Promise<{ available: boolean }> => {
    try {
      const response = await api.get<StandardResponse>(`/auth/check-email?email=${email}`)
      return { available: true }
    } catch (error: any) {
      if (error.response?.status === 409) {
        return { available: false }
      }
      throw error
    }
  },

  logout: async (): Promise<void> => {
    // 백엔드에 로그아웃 엔드포인트가 없으므로 클라이언트에서만 처리
    useAuthStore().clearAuth()
  },
}
