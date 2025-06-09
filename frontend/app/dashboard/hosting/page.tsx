"use client"

import { useState } from "react"
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
import { Server, Terminal, Trash2, Copy, ExternalLink, Plus, Loader2 } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { CreateHostingDialog } from "@/components/dashboard/create-hosting-dialog"
import { SSHInfoDialog } from "@/components/dashboard/ssh-info-dialog"

const statusConfig = {
  creating: { label: "생성 중", color: "bg-blue-500", icon: Loader2 },
  running: { label: "실행 중", color: "bg-green-500", icon: Server },
  stopping: { label: "중지 중", color: "bg-yellow-500", icon: Loader2 },
  stopped: { label: "중지됨", color: "bg-gray-500", icon: Server },
  error: { label: "오류", color: "bg-red-500", icon: Server },
}

export default function HostingPage() {
  const { instances, isLoading, createInstance, deleteInstance } = useHosting()
  const { showSuccess } = useToast()
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [sshDialogOpen, setSshDialogOpen] = useState(false)
  const [selectedInstance, setSelectedInstance] = useState<any>(null)

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text)
    showSuccess(`${label}이(가) 클립보드에 복사되었습니다!`)
  }

  const handleCreateHosting = async (data: any) => {
    try {
      await createInstance(data)
      setCreateDialogOpen(false)
    } catch (error) {
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

  const openSSHDialog = (instance: any) => {
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
