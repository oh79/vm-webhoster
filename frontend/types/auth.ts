export interface User {
  id: number
  email: string
  username: string
  is_active: boolean
  created_at: string
}

export interface LoginRequest {
  username: string // FastAPI OAuth2PasswordRequestForm은 username 필드를 사용
  password: string
}

export interface RegisterRequest {
  email: string
  username: string
  password: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export interface StandardResponse<T = any> {
  success: boolean
  message: string
  data?: T
}
