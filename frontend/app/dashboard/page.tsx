"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Server, CheckCircle, ExternalLink, Plus } from "lucide-react"
import Link from "next/link"
import { useAuthStore } from "@/store/auth-store"
import { useHosting } from "@/hooks/use-hosting"
import { useEffect, useState } from "react"
import { Skeleton } from "@/components/ui/skeleton"

export default function DashboardPage() {
  const { user } = useAuthStore()
  const { instances, isLoading } = useHosting()
  const [stats, setStats] = useState({
    activeInstances: 0,
    serverStatus: "대기 중",
  })

  useEffect(() => {
    // Calculate stats based on instances
    if (!isLoading) {
      const activeCount = instances.filter((instance) => instance.status === "running").length
      
      // 첫 번째 인스턴스 기준으로 정보 계산
      const firstInstance = instances[0]
      let serverStatus = "대기 중"

      if (firstInstance) {
        // 서버 상태
        serverStatus = firstInstance.status === "running" ? "정상 운영" : 
                     firstInstance.status === "creating" ? "생성 중" :
                     firstInstance.status === "error" ? "오류 발생" : "중지됨"
      }

      setStats({
        activeInstances: activeCount,
        serverStatus: serverStatus,
      })
    }
  }, [instances, isLoading])

  const statItems = [
    {
      title: "활성 호스팅",
      value: stats.activeInstances.toString(),
      description: "실행 중인 인스턴스",
      icon: Server,
      color: "text-green-600",
    },
    {
      title: "서버 상태",
      value: stats.serverStatus,
      description: "현재 운영 상태",
      icon: CheckCircle,
      color: stats.serverStatus === "정상 운영" ? "text-emerald-600" : 
             stats.serverStatus === "생성 중" ? "text-yellow-600" : 
             stats.serverStatus === "오류 발생" ? "text-red-600" : "text-gray-600",
    },
  ]

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold">대시보드</h1>
            <Skeleton className="h-4 w-48 mt-2" />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[1, 2].map((i) => (
            <Card key={i}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-4 w-4" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-16 mb-2" />
                <Skeleton className="h-3 w-20" />
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <Skeleton className="h-6 w-32" />
              <Skeleton className="h-4 w-48" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-32 w-full" />
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <Skeleton className="h-6 w-32" />
              <Skeleton className="h-4 w-48" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-32 w-full" />
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">대시보드</h1>
          <p className="text-gray-600 dark:text-gray-400">
            안녕하세요, {user?.username || "사용자"}님! 호스팅 현황을 확인해보세요.
          </p>
        </div>
      </div>

      {/* Stats Grid - 2개 카드로 더 크게 표시 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {statItems.map((item, index) => {
          const Icon = item.icon
          return (
            <Card key={index} className="p-2">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
                <CardTitle className="text-base font-medium">{item.title}</CardTitle>
                <Icon className={`h-6 w-6 ${item.color}`} />
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold mb-2">{item.value}</div>
                <p className="text-sm text-gray-500 dark:text-gray-400">{item.description}</p>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>빠른 작업</CardTitle>
            <CardDescription>자주 사용하는 기능들에 빠르게 접근하세요</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 gap-3">
              <Button asChild className="justify-start h-auto p-4">
                <Link href="/dashboard/hosting">
                  <div className="flex items-center gap-3">
                    <Server className="h-5 w-5" />
                    <div className="text-left">
                      <div className="font-medium">호스팅 관리</div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        인스턴스 생성, 관리 및 모니터링
                      </div>
                    </div>
                  </div>
                </Link>
              </Button>

              {instances.length > 0 && instances[0].status === "running" && (
                <Button asChild variant="outline" className="justify-start h-auto p-4">
                  <Link href={`http://localhost/${user?.id || '1'}`} target="_blank">
                    <div className="flex items-center gap-3">
                      <ExternalLink className="h-5 w-5" />
                      <div className="text-left">
                        <div className="font-medium">내 웹사이트 보기</div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          호스팅된 웹사이트를 새 탭에서 열기
                        </div>
                      </div>
                    </div>
                  </Link>
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card>
          <CardHeader>
            <CardTitle>최근 활동</CardTitle>
            <CardDescription>최근 호스팅 관련 활동 내역</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {instances.length > 0 ? (
                <div className="space-y-3">
                  {instances.map((instance) => (
                    <div key={instance.id} className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <Server className="h-4 w-4 text-blue-500" />
                      <div className="flex-1">
                        <p className="text-sm font-medium">VM-{instance.vm_id}</p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          상태: {instance.status === "running" ? "실행 중" : 
                                instance.status === "creating" ? "생성 중" : 
                                instance.status === "error" ? "오류" : instance.status}
                        </p>
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {new Date(instance.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Server className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                  <p className="text-gray-500 dark:text-gray-400 mb-4">아직 활동 내역이 없습니다</p>
                  <Button asChild size="sm">
                    <Link href="/dashboard/hosting">
                      <Plus className="mr-2 h-4 w-4" />
                      첫 번째 호스팅 생성하기
                    </Link>
                  </Button>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
