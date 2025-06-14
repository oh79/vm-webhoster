"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Server, Globe, Shield, Activity, ExternalLink, Plus, CreditCard, Bell } from "lucide-react"
import Link from "next/link"
import { useAuthStore } from "@/store/auth-store"
import { useHosting } from "@/hooks/use-hosting"
import { useEffect, useState } from "react"
import { Skeleton } from "@/components/ui/skeleton"
import { useNotificationStore } from "@/store/notification-store"

export default function DashboardPage() {
  const { user } = useAuthStore()
  const { instances, isLoading } = useHosting()
  const { notifications } = useNotificationStore()
  const [stats, setStats] = useState({
    activeInstances: 0,
    totalVisits: "0",
    uptime: "0%",
    bandwidth: "0 GB",
  })

  useEffect(() => {
    // Calculate stats based on instances
    if (!isLoading) {
      const activeCount = instances.filter((instance) => instance.status === "running").length

      // In a real app, these would come from your API
      setStats({
        activeInstances: activeCount,
        totalVisits: "2,847",
        uptime: "99.9%",
        bandwidth: "12.4 GB",
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
      title: "총 방문자",
      value: stats.totalVisits,
      description: "이번 달",
      icon: Globe,
      color: "text-blue-600",
    },
    {
      title: "가동 시간",
      value: stats.uptime,
      description: "최근 30일",
      icon: Shield,
      color: "text-emerald-600",
    },
    {
      title: "대역폭",
      value: stats.bandwidth,
      description: "이번 달 사용량",
      icon: Activity,
      color: "text-purple-600",
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">대시보드</h1>
        <p className="text-gray-600 dark:text-gray-400">환영합니다, {user?.username}님! 호스팅 현황을 확인하세요.</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {isLoading
          ? Array(4)
              .fill(0)
              .map((_, i) => (
                <Card key={i}>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <Skeleton className="h-4 w-24" />
                    <Skeleton className="h-4 w-4 rounded-full" />
                  </CardHeader>
                  <CardContent>
                    <Skeleton className="h-8 w-16 mb-2" />
                    <Skeleton className="h-4 w-32" />
                  </CardContent>
                </Card>
              ))
          : statItems.map((stat) => (
              <Card key={stat.title}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
                  <stat.icon className={`h-4 w-4 ${stat.color}`} />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stat.value}</div>
                  <p className="text-xs text-muted-foreground">{stat.description}</p>
                </CardContent>
              </Card>
            ))}
      </div>

      {/* Quick Actions and Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Hosting Instances */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>호스팅 인스턴스</CardTitle>
              <CardDescription>활성화된 호스팅 서비스</CardDescription>
            </div>
            <Button asChild size="sm">
              <Link href="/dashboard/hosting">
                <Plus className="h-4 w-4 mr-2" />새 인스턴스
              </Link>
            </Button>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-4">
                {Array(3)
                  .fill(0)
                  .map((_, i) => (
                    <div key={i} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <Skeleton className="h-8 w-8 rounded-full" />
                        <div>
                          <Skeleton className="h-4 w-24 mb-1" />
                          <Skeleton className="h-3 w-16" />
                        </div>
                      </div>
                      <Skeleton className="h-8 w-8 rounded-full" />
                    </div>
                  ))}
              </div>
            ) : instances.length === 0 ? (
              <div className="text-center py-6">
                <Server className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium mb-2">호스팅 인스턴스가 없습니다</h3>
                <p className="text-gray-500 mb-4">첫 번째 호스팅 인스턴스를 생성해보세요</p>
                <Button asChild>
                  <Link href="/dashboard/hosting">
                    <Plus className="h-4 w-4 mr-2" />
                    호스팅 생성
                  </Link>
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                {instances.slice(0, 3).map((instance) => (
                  <div key={instance.id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-2 h-2 rounded-full ${
                          instance.status === "running"
                            ? "bg-green-500"
                            : instance.status === "creating" || instance.status === "stopping"
                              ? "bg-blue-500"
                              : instance.status === "error"
                                ? "bg-red-500"
                                : "bg-gray-500"
                        }`}
                      ></div>
                      <div>
                        <p className="font-medium">VM-{instance.vmId}</p>
                        <p className="text-xs text-gray-500">
                          {instance.status === "running"
                            ? "실행 중"
                            : instance.status === "creating"
                              ? "생성 중"
                              : instance.status === "stopping"
                                ? "중지 중"
                                : instance.status === "stopped"
                                  ? "중지됨"
                                  : "오류"}
                        </p>
                      </div>
                    </div>
                    <Button variant="ghost" size="icon" asChild>
                      <Link href={`/dashboard/hosting/${instance.id}`}>
                        <ExternalLink className="h-4 w-4" />
                      </Link>
                    </Button>
                  </div>
                ))}
                {instances.length > 3 && (
                  <Button variant="outline" asChild className="w-full">
                    <Link href="/dashboard/hosting">모든 인스턴스 보기</Link>
                  </Button>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>최근 활동</CardTitle>
              <CardDescription>최신 알림 및 이벤트</CardDescription>
            </div>
            <Button variant="outline" size="icon">
              <Bell className="h-4 w-4" />
            </Button>
          </CardHeader>
          <CardContent>
            {notifications.length === 0 ? (
              <div className="text-center py-6">
                <Bell className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium mb-2">최근 활동 없음</h3>
                <p className="text-gray-500">최근 활동이 여기에 표시됩니다</p>
              </div>
            ) : (
              <div className="space-y-4">
                {notifications.slice(0, 4).map((notification) => (
                  <div
                    key={notification.id}
                    className={`flex items-center space-x-4 p-3 border rounded-lg ${
                      !notification.read ? "bg-blue-50 dark:bg-blue-900/20" : ""
                    }`}
                  >
                    <div
                      className={`w-2 h-2 rounded-full ${
                        notification.type === "success"
                          ? "bg-green-500"
                          : notification.type === "warning"
                            ? "bg-yellow-500"
                            : notification.type === "error"
                              ? "bg-red-500"
                              : "bg-blue-500"
                      }`}
                    ></div>
                    <div className="flex-1">
                      <p className="text-sm font-medium">{notification.title}</p>
                      <p className="text-xs text-gray-500">
                        {new Date(notification.createdAt).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Billing Summary */}
      <Card>
        <CardHeader>
          <CardTitle>결제 요약</CardTitle>
          <CardDescription>현재 요금제 및 결제 정보</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <CreditCard className="h-8 w-8 text-blue-500" />
              <div>
                <h3 className="font-medium">스탠다드 요금제</h3>
                <p className="text-sm text-gray-500">월 29,900원 • 다음 결제일: 2023년 8월 1일</p>
              </div>
            </div>
            <Button asChild variant="outline">
              <Link href="/dashboard/billing">결제 관리</Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
