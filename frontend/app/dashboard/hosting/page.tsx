"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { Dialog, DialogTrigger } from "@/components/ui/dialog"
import { useHosting } from "@/hooks/use-hosting"
import { Server, Terminal, Trash2, Copy, ExternalLink, Plus, Loader2, CheckCircle } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { CreateHostingDialog } from "@/components/dashboard/create-hosting-dialog"
import { SSHInfoDialog } from "@/components/dashboard/ssh-info-dialog"
import type { HostingInstance } from "@/types/hosting"

const statusConfig = {
  creating: { label: "생성 중", color: "bg-blue-500", icon: Loader2 },
  running: { label: "실행 중", color: "bg-green-500", icon: Server },
  stopping: { label: "중지 중", color: "bg-yellow-500", icon: Loader2 },
  stopped: { label: "중지됨", color: "bg-gray-500", icon: Server },
  error: { label: "오류", color: "bg-red-500", icon: Server },
}

export default function HostingPage() {
  const router = useRouter()
  const { instances, isLoading, createInstance, deleteInstance, fetchInstances } = useHosting()
  const { showSuccess } = useToast()
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [sshDialogOpen, setSshDialogOpen] = useState(false)
  const [selectedInstance, setSelectedInstance] = useState<HostingInstance | null>(null)
  // 호스팅 생성 후 로딩 상태 관리
  const [isCreatingHosting, setIsCreatingHosting] = useState(false)
  const [creationProgress, setCreationProgress] = useState(0)

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text)
    showSuccess(`${label}이(가) 클립보드에 복사되었습니다!`)
  }

  const handleCreateHosting = async (data: any) => {
    try {
      setIsCreatingHosting(true)
      setCreationProgress(0)
      
      // 프로그레스 바 애니메이션 시작
      const progressInterval = setInterval(() => {
        setCreationProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval)
            return 90
          }
          return prev + 10
        })
      }, 1000)

      await createInstance(data)
      setCreateDialogOpen(false)
      
      // 생성 완료 후 진행률을 100%로 설정
      setCreationProgress(100)
      
      // 10초 후 상태 리셋 및 데이터 재로드
      setTimeout(async () => {
        try {
          setIsCreatingHosting(false)
          setCreationProgress(0)
          
          // 데이터 다시 불러오기
          await fetchInstances()
          showSuccess("🎉 호스팅 인스턴스 생성이 완료되었습니다!")
          
        } catch (error) {
          console.error("Failed to refresh data:", error)
          
          // 데이터 로드 실패 시 사용자에게 알림 후 대체 방법 시도
          showSuccess("호스팅 생성이 완료되었습니다. 페이지를 새로고침합니다.")
          
          // Next.js 라우터의 refresh 사용 (안전한 새로고침)
          router.refresh()
        }
      }, 10000)
      
    } catch (error) {
      setIsCreatingHosting(false)
      setCreationProgress(0)
      // Error is handled in the hook
    }
  }

  const handleDeleteInstance = async () => {
    try {
      await deleteInstance()
    } catch (error) {
      // Error is handled in the hook
    }
  }

  const openSSHDialog = (instance: HostingInstance) => {
    setSelectedInstance(instance)
    setSshDialogOpen(true)
  }

  // 백엔드 응답에서 web_url과 ssh_command가 없는 경우 생성
  const getWebUrl = (instance: any) => {
    return instance.web_url || `http://${instance.vm_ip}`
  }

  const getSSHCommand = (instance: any) => {
    return instance.ssh_command || `ssh -p ${instance.ssh_port} user@${instance.vm_ip}`
  }

  // 호스팅 생성 중 로딩 화면
  if (isCreatingHosting) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center max-w-lg mx-auto p-8">
          <div className="mb-8">
            <Loader2 className="mx-auto h-16 w-16 text-blue-500 animate-spin mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              호스팅 인스턴스 생성 중...
            </h2>
            <p className="text-gray-600 dark:text-gray-400">
              새로운 호스팅 환경을 준비하고 있습니다. 잠시만 기다려주세요.
            </p>
          </div>

          {/* 프로그레스 바 */}
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mb-4">
            <div 
              className="bg-blue-500 h-2 rounded-full transition-all duration-1000 ease-out"
              style={{ width: `${creationProgress}%` }}
            />
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
            진행률: {creationProgress}%
          </p>

          {/* 생성 단계 표시 */}
          <div className="space-y-3 text-left">
            <div className="flex items-center gap-3">
              <CheckCircle className="h-5 w-5 text-green-500" />
              <span className="text-sm text-gray-700 dark:text-gray-300">가상 머신 할당 완료</span>
            </div>
            <div className="flex items-center gap-3">
              <CheckCircle className="h-5 w-5 text-green-500" />
              <span className="text-sm text-gray-700 dark:text-gray-300">운영체제 설치 완료</span>
            </div>
            <div className="flex items-center gap-3">
              {creationProgress >= 70 ? (
                <CheckCircle className="h-5 w-5 text-green-500" />
              ) : (
                <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />
              )}
              <span className="text-sm text-gray-700 dark:text-gray-300">웹 서버 설정 중...</span>
            </div>
            <div className="flex items-center gap-3">
              {creationProgress >= 90 ? (
                <CheckCircle className="h-5 w-5 text-green-500" />
              ) : (
                <div className="h-5 w-5 border-2 border-gray-300 dark:border-gray-600 rounded-full" />
              )}
              <span className="text-sm text-gray-700 dark:text-gray-300">최종 설정 중...</span>
            </div>
          </div>

          <div className="mt-8 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <p className="text-sm text-blue-800 dark:text-blue-200">
              💡 생성이 완료되면 자동으로 "내 호스팅" 페이지로 이동합니다. (약 10초 소요)
            </p>
          </div>
        </div>
      </div>
    )
  }

  if (isLoading && instances.length === 0) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold">내 호스팅</h1>
          <Skeleton className="h-10 w-32" />
        </div>
        <div className="grid gap-6">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-6 w-48" />
                <Skeleton className="h-4 w-32" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-20 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  if (instances.length === 0) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold">내 호스팅</h1>
        </div>

        {/* Empty State */}
        <div className="text-center py-12">
          <Server className="mx-auto h-24 w-24 text-gray-400 mb-6" />
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">아직 호스팅 인스턴스가 없습니다</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-8 max-w-md mx-auto">
            첫 번째 호스팅 인스턴스를 생성해보세요. 몇 분 안에 설정이 완료됩니다.
          </p>
          <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button size="lg" className="px-8">
                <Plus className="mr-2 h-5 w-5" />첫 번째 호스팅 생성하기
              </Button>
            </DialogTrigger>
            <CreateHostingDialog onSubmit={handleCreateHosting} />
          </Dialog>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">내 호스팅</h1>
        <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              호스팅 생성
            </Button>
          </DialogTrigger>
          <CreateHostingDialog onSubmit={handleCreateHosting} />
        </Dialog>
      </div>

      <div className="grid gap-6">
        {instances.map((instance) => {
          const status = statusConfig[instance.status]
          const StatusIcon = status.icon

          return (
            <Card key={instance.id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-3">
                      VM-{instance.vm_id}
                      <Badge variant="secondary" className="flex items-center gap-1">
                        <div className={`w-2 h-2 rounded-full ${status.color}`} />
                        {status.label}
                        {(instance.status === "creating" || instance.status === "stopping") && (
                          <StatusIcon className="h-3 w-3 animate-spin ml-1" />
                        )}
                      </Badge>
                    </CardTitle>
                    <CardDescription>생성일: {new Date(instance.created_at).toLocaleDateString()}</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                  <div>
                    <label className="text-sm font-medium text-gray-500 dark:text-gray-400">웹 URL</label>
                    <div className="flex items-center gap-2 mt-1">
                      <code className="flex-1 px-3 py-2 bg-gray-100 dark:bg-gray-800 rounded text-sm">
                        {getWebUrl(instance)}
                      </code>
                      <Button size="sm" variant="outline" onClick={() => copyToClipboard(getWebUrl(instance), "웹 URL")}>
                        <Copy className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500 dark:text-gray-400">SSH 연결</label>
                    <div className="flex items-center gap-2 mt-1">
                      <code className="flex-1 px-3 py-2 bg-gray-100 dark:bg-gray-800 rounded text-sm">
                        {getSSHCommand(instance)}
                      </code>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() =>
                          copyToClipboard(getSSHCommand(instance), "SSH 정보")
                        }
                      >
                        <Copy className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>

                <div className="flex gap-2 flex-wrap">
                  <Button
                    variant="outline"
                    onClick={() => window.open(getWebUrl(instance), "_blank")}
                    disabled={instance.status !== "running"}
                  >
                    <ExternalLink className="mr-2 h-4 w-4" />
                    사이트 보기
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => openSSHDialog(instance)}
                    disabled={instance.status !== "running"}
                  >
                    <Terminal className="mr-2 h-4 w-4" />
                    SSH 정보
                  </Button>
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button variant="destructive">
                        <Trash2 className="mr-2 h-4 w-4" />
                        삭제
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>호스팅 인스턴스 삭제</AlertDialogTitle>
                        <AlertDialogDescription>
                          VM-{instance.vm_id}을(를) 삭제하시겠습니까? 이 작업은 되돌릴 수 없으며 모든 데이터가
                          손실됩니다.
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>취소</AlertDialogCancel>
                        <AlertDialogAction
                          onClick={() => handleDeleteInstance()}
                          className="bg-red-600 hover:bg-red-700"
                        >
                          삭제
                        </AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* SSH Info Dialog */}
      <Dialog open={sshDialogOpen} onOpenChange={setSshDialogOpen}>
        <SSHInfoDialog instance={selectedInstance} />
      </Dialog>
    </div>
  )
}
