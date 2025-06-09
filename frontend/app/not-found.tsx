"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { FileQuestion, Home, ArrowLeft } from "lucide-react"
import Link from "next/link"

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <FileQuestion className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <CardTitle>페이지를 찾을 수 없습니다</CardTitle>
          <CardDescription>찾으시는 페이지가 존재하지 않거나 이동되었습니다.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button asChild className="w-full">
            <Link href="/">
              <Home className="mr-2 h-4 w-4" />
              홈으로 이동
            </Link>
          </Button>
          <Button asChild variant="outline" className="w-full" onClick={() => window.history.back()}>
            <span>
              <ArrowLeft className="mr-2 h-4 w-4" />
              이전으로 돌아가기
            </span>
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
