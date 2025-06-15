"use client"

import { useState } from "react"
import { DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Loader2, Server, CheckCircle } from "lucide-react"
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
      setIsLoading(false)
    }
    // 성공 시에는 부모 컴포넌트에서 로딩 상태를 관리하므로 여기서는 setIsLoading(false)를 하지 않음
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
          <h4 className="font-medium mb-2 flex items-center gap-2">
            <Server className="h-4 w-4" />
            포함된 기능:
          </h4>
          <ul className="text-sm space-y-2">
            <li className="flex items-center gap-2">
              <CheckCircle className="h-3 w-3 text-green-500" />
              Ubuntu 22.04 LTS 운영체제
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle className="h-3 w-3 text-green-500" />
              Nginx 웹 서버 자동 설치
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle className="h-3 w-3 text-green-500" />
              SSH 접속 지원
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle className="h-3 w-3 text-green-500" />
              1GB RAM, 1 CPU Core
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle className="h-3 w-3 text-green-500" />
              전용 IP 주소
            </li>
          </ul>
        </div>

        {isLoading && (
          <div className="bg-yellow-50 dark:bg-yellow-900/20 p-4 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Loader2 className="h-4 w-4 animate-spin text-yellow-600" />
              <span className="font-medium text-yellow-800 dark:text-yellow-200">생성 요청 처리 중...</span>
            </div>
            <p className="text-sm text-yellow-700 dark:text-yellow-300">
              호스팅 인스턴스 생성이 시작되었습니다. 잠시 후 전체 화면 로딩 상태로 전환됩니다.
            </p>
          </div>
        )}

        <div className="flex justify-end gap-2 pt-4">
          <Button onClick={handleSubmit} disabled={isLoading} size="lg">
            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {isLoading ? "생성 중..." : "호스팅 생성"}
          </Button>
        </div>

        {!isLoading && (
          <div className="text-xs text-gray-500 dark:text-gray-400 text-center">
            💡 생성 후 자동으로 진행 상황을 확인할 수 있습니다.
          </div>
        )}
      </div>
    </DialogContent>
  )
}
