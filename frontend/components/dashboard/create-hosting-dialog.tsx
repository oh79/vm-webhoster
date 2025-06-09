"use client"

import { useState } from "react"
import { DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Loader2 } from "lucide-react"
import type { CreateHostingRequest } from "@/types/hosting"

interface CreateHostingDialogProps {
  onSubmit: (data: CreateHostingRequest) => Promise<void>
}

export function CreateHostingDialog({ onSubmit }: CreateHostingDialogProps) {
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async () => {
    setIsLoading(true)
    try {
      await onSubmit({}) // 백엔드에서 현재 사용자 기반으로 생성
    } catch (error) {
      // Error is handled by parent
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <DialogContent>
      <DialogHeader>
        <DialogTitle>새 호스팅 인스턴스 생성</DialogTitle>
        <DialogDescription>
          웹 호스팅을 위한 새 가상 머신을 설정합니다. 생성에는 몇 분이 소요될 수 있습니다.
        </DialogDescription>
      </DialogHeader>

      <div className="space-y-4">
        <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
          <h4 className="font-medium mb-2">포함된 기능:</h4>
          <ul className="text-sm space-y-1">
            <li>• Ubuntu 20.04 LTS 운영체제</li>
            <li>• Nginx 웹 서버 자동 설치</li>
            <li>• SSH 접속 지원</li>
            <li>• 1GB RAM, 1 CPU Core</li>
            <li>• 전용 IP 주소</li>
          </ul>
        </div>

        <div className="flex justify-end gap-2 pt-4">
          <Button onClick={handleSubmit} disabled={isLoading}>
            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            호스팅 생성
          </Button>
        </div>
      </div>
    </DialogContent>
  )
}
