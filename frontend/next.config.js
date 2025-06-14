/** @type {import('next').NextConfig} */
const nextConfig = {
  // 외부 접근 허용
  experimental: {
    serverComponentsExternalPackages: [],
  },
  
  // API 리라이트 설정 (VM 환경용)
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL}/api/:path*`,
      },
    ];
  },
  
  // 환경별 설정
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
};

module.exports = nextConfig; 