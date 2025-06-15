import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// API 설정: 개발 환경에서는 백엔드 직접 호출, 운영 환경에서는 Nginx 프록시 사용
export const API_BASE_URL = process.env.NODE_ENV === 'development' 
  ? process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"
  : "/api/v1"
