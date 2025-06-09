import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Navbar } from "@/components/layout/navbar"
import { Server, Shield, Zap } from "lucide-react"

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <Navbar />
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 dark:text-white mb-6">웹 호스팅 서비스</h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 mb-8 max-w-2xl mx-auto">
            비즈니스를 위한 전문적이고 안정적이며 빠른 웹 호스팅 솔루션
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <Button asChild size="lg">
              <Link href="/auth/register">시작하기</Link>
            </Button>
            <Button asChild variant="outline" size="lg">
              <Link href="/auth/login">로그인</Link>
            </Button>
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
          <Card className="text-center">
            <CardHeader>
              <Server className="h-12 w-12 text-blue-600 mb-4 mx-auto" />
              <CardTitle>안정적인 인프라</CardTitle>
              <CardDescription>99.9% 가동 시간 보장, 기업용 서버 및 24/7 모니터링</CardDescription>
            </CardHeader>
          </Card>

          <Card className="text-center">
            <CardHeader>
              <Shield className="h-12 w-12 text-green-600 mb-4 mx-auto" />
              <CardTitle>안전한 호스팅</CardTitle>
              <CardDescription>고급 보안 기능, SSL 인증서 및 자동 백업 포함</CardDescription>
            </CardHeader>
          </Card>

          <Card className="text-center">
            <CardHeader>
              <Zap className="h-12 w-12 text-yellow-600 mb-4 mx-auto" />
              <CardTitle>빠른 속도</CardTitle>
              <CardDescription>글로벌 CDN 네트워크와 SSD 스토리지로 최적화된 성능</CardDescription>
            </CardHeader>
          </Card>
        </div>
      </div>
    </div>
  )
}
