"use client"

import { DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Copy } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import type { HostingInstance } from "@/types/hosting"

interface SSHInfoDialogProps {
  instance: HostingInstance | null
}

export function SSHInfoDialog({ instance }: SSHInfoDialogProps) {
  const { showSuccess } = useToast()

  if (!instance) return null

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text)
    showSuccess(`${label}이(가) 클립보드에 복사되었습니다!`)
  }

  const sshCommand = `ssh ${instance.sshInfo.username}@${instance.sshInfo.host} -p ${instance.sshInfo.port}`

  return (
    <DialogContent>
      <DialogHeader>
        <DialogTitle>SSH 연결 정보</DialogTitle>
        <DialogDescription>SSH를 통해 호스팅 인스턴스에 연결하기 위한 정보입니다.</DialogDescription>
      </DialogHeader>

      <div className="space-y-4">
        <div>
          <label className="text-sm font-medium text-gray-500 dark:text-gray-400">호스트</label>
          <div className="flex items-center gap-2 mt-1">
            <code className="flex-1 px-3 py-2 bg-gray-100 dark:bg-gray-800 rounded text-sm">
              {instance.sshInfo.host}
            </code>
            <Button size="sm" variant="outline" onClick={() => copyToClipboard(instance.sshInfo.host, "호스트")}>
              <Copy className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div>
          <label className="text-sm font-medium text-gray-500 dark:text-gray-400">포트</label>
          <div className="flex items-center gap-2 mt-1">
            <code className="flex-1 px-3 py-2 bg-gray-100 dark:bg-gray-800 rounded text-sm">
              {instance.sshInfo.port}
            </code>
            <Button
              size="sm"
              variant="outline"
              onClick={() => copyToClipboard(instance.sshInfo.port.toString(), "포트")}
            >
              <Copy className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div>
          <label className="text-sm font-medium text-gray-500 dark:text-gray-400">사용자 이름</label>
          <div className="flex items-center gap-2 mt-1">
            <code className="flex-1 px-3 py-2 bg-gray-100 dark:bg-gray-800 rounded text-sm">
              {instance.sshInfo.username}
            </code>
            <Button
              size="sm"
              variant="outline"
              onClick={() => copyToClipboard(instance.sshInfo.username, "사용자 이름")}
            >
              <Copy className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div>
          <label className="text-sm font-medium text-gray-500 dark:text-gray-400">전체 SSH 명령어</label>
          <div className="flex items-center gap-2 mt-1">
            <code className="flex-1 px-3 py-2 bg-gray-100 dark:bg-gray-800 rounded text-sm">{sshCommand}</code>
            <Button size="sm" variant="outline" onClick={() => copyToClipboard(sshCommand, "SSH 명령어")}>
              <Copy className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </DialogContent>
  )
}
