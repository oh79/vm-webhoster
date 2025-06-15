"use client"

import { useState } from "react"
import { DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Copy, Download, Eye, EyeOff } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import type { HostingInstance } from "@/types/hosting"

interface SSHInfoDialogProps {
  instance: HostingInstance | null
}

export function SSHInfoDialog({ instance }: SSHInfoDialogProps) {
  const [showPrivateKey, setShowPrivateKey] = useState(false)
  const { showSuccess } = useToast()

  if (!instance) {
    return (
      <DialogContent>
        <DialogHeader>
          <DialogTitle>SSH 연결 정보</DialogTitle>
          <DialogDescription>
            호스팅 인스턴스 정보를 불러오는 중입니다...
          </DialogDescription>
        </DialogHeader>
        <div className="p-4 text-center text-gray-500">
          인스턴스 정보를 불러오는 중입니다.
        </div>
      </DialogContent>
    )
  }

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text)
    showSuccess(`${label}이(가) 클립보드에 복사되었습니다!`)
  }

  const sshCommand = instance.ssh_command || `ssh -p ${instance.ssh_port} ubuntu@localhost`
  const sftpCommand = `sftp -P ${instance.ssh_port} ubuntu@localhost`

  return (
    <DialogContent>
      <DialogHeader>
        <DialogTitle>SSH 연결 정보</DialogTitle>
        <DialogDescription>
          VM-{instance.vm_id}에 SSH로 연결하기 위한 정보입니다.
        </DialogDescription>
      </DialogHeader>

      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="ssh-command">SSH 연결 명령어</Label>
          <div className="flex gap-2">
            <Input
              id="ssh-command"
              value={sshCommand}
              readOnly
              className="font-mono text-sm"
            />
            <Button
              variant="outline"
              size="icon"
              onClick={() => copyToClipboard(sshCommand, "SSH 명령어")}
            >
              <Copy className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="sftp-command">SFTP 연결 명령어</Label>
          <div className="flex gap-2">
            <Input
              id="sftp-command"
              value={sftpCommand}
              readOnly
              className="font-mono text-sm"
            />
            <Button
              variant="outline"
              size="icon"
              onClick={() => copyToClipboard(sftpCommand, "SFTP 명령어")}
            >
              <Copy className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="host">호스트</Label>
          <div className="flex gap-2">
            <Input
              id="host"
              value="localhost"
              readOnly
              className="font-mono text-sm"
            />
            <Button
              variant="outline"
              size="icon"
              onClick={() => copyToClipboard("localhost", "호스트")}
            >
              <Copy className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="port">포트</Label>
          <div className="flex gap-2">
            <Input
              id="port"
              value={instance.ssh_port.toString()}
              readOnly
              className="font-mono text-sm"
            />
            <Button
              variant="outline"
              size="icon"
              onClick={() => copyToClipboard(instance.ssh_port.toString(), "포트")}
            >
              <Copy className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="username">사용자명</Label>
          <div className="flex gap-2">
            <Input
              id="username"
              value="ubuntu"
              readOnly
              className="font-mono text-sm"
            />
            <Button
              variant="outline"
              size="icon"
              onClick={() => copyToClipboard("ubuntu", "사용자명")}
            >
              <Copy className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
          <h4 className="font-medium mb-2">연결 방법:</h4>
          <ol className="text-sm space-y-1 list-decimal list-inside">
            <li>터미널을 열고 위의 SSH 명령어를 복사하여 붙여넣기</li>
            <li>Enter 키를 눌러 연결</li>
            <li>처음 연결 시 호스트 키 확인 메시지가 나오면 'yes' 입력</li>
            <li>비밀번호 없이 자동으로 로그인됩니다</li>
          </ol>
        </div>
      </div>
    </DialogContent>
  )
}
