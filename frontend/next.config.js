/** @type {import('next').NextConfig} */
const nextConfig = {
  // 외부 패키지 설정 (Next.js 15 호환)
  serverExternalPackages: [],
  
  // 환경별 설정 (API URL은 Nginx를 통해 직접 호출)
  env: {
    // Docker 환경에서는 Nginx를 통해 API 호출
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || '',
  },
};

module.exports = nextConfig; 