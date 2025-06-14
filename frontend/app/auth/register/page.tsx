"use client"

import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Checkbox } from "@/components/ui/checkbox"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Progress } from "@/components/ui/progress"
import { useToast } from "@/hooks/use-toast"
import api from "@/lib/api"
import { Loader2, Check, X } from "lucide-react"
import { useEmailCheck } from "@/hooks/use-email-check"

const registerSchema = z
  .object({
    email: z.string().email("유효한 이메일 주소를 입력해주세요"),
    username: z.string().min(3, "사용자 이름은 최소 3자 이상이어야 합니다"),
    password: z
      .string()
      .min(8, "비밀번호는 최소 8자 이상이어야 합니다")
      .regex(/^(?=.*[a-zA-Z])(?=.*\d)/, "비밀번호는 문자와 숫자를 모두 포함해야 합니다"),
    confirmPassword: z.string(),
    acceptTerms: z.boolean().refine((val) => val === true, "서비스 이용약관에 동의해야 합니다"),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "비밀번호가 일치하지 않습니다",
    path: ["confirmPassword"],
  })

type RegisterForm = z.infer<typeof registerSchema>

export default function RegisterPage() {
  const [isLoading, setIsLoading] = useState(false)
  const router = useRouter()
  const { showSuccess, showError } = useToast()

  const form = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: "",
      username: "",
      password: "",
      confirmPassword: "",
      acceptTerms: false,
    },
  })

  const watchedEmail = form.watch("email")
  const watchedPassword = form.watch("password")
  const { emailAvailable, checkingEmail } = useEmailCheck(watchedEmail)

  // 비밀번호 강도 계산
  const getPasswordStrength = (password: string) => {
    let strength = 0
    if (password.length >= 8) strength += 25
    if (/[a-z]/.test(password)) strength += 25
    if (/[A-Z]/.test(password)) strength += 25
    if (/\d/.test(password)) strength += 25
    return strength
  }

  const passwordStrength = getPasswordStrength(watchedPassword)

  const onSubmit = async (data: RegisterForm) => {
    setIsLoading(true)
    try {
      await api.post("/auth/register", data)
      showSuccess("회원가입이 완료되었습니다! 이메일을 확인하여 계정을 인증해주세요.")
      router.push("/auth/login")
    } catch (error: any) {
      const message = error.response?.data?.message || "회원가입에 실패했습니다. 다시 시도해주세요."
      showError(message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold">계정 생성</CardTitle>
          <CardDescription>웹 호스팅 서비스에 가입하세요</CardDescription>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>이메일</FormLabel>
                    <FormControl>
                      <div className="relative">
                        <Input type="email" placeholder="이메일 주소 입력" {...field} />
                        {checkingEmail && <Loader2 className="absolute right-3 top-3 h-4 w-4 animate-spin" />}
                        {!checkingEmail && emailAvailable === true && (
                          <Check className="absolute right-3 top-3 h-4 w-4 text-green-500" />
                        )}
                        {!checkingEmail && emailAvailable === false && (
                          <X className="absolute right-3 top-3 h-4 w-4 text-red-500" />
                        )}
                      </div>
                    </FormControl>
                    {emailAvailable === false && <p className="text-sm text-red-500">이미 사용 중인 이메일입니다</p>}
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="username"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>사용자 이름</FormLabel>
                    <FormControl>
                      <Input placeholder="사용자 이름 입력" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>비밀번호</FormLabel>
                    <FormControl>
                      <Input type="password" placeholder="비밀번호 입력" {...field} />
                    </FormControl>
                    {watchedPassword && (
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span>비밀번호 강도:</span>
                          <span
                            className={
                              passwordStrength < 50
                                ? "text-red-500"
                                : passwordStrength < 75
                                  ? "text-yellow-500"
                                  : "text-green-500"
                            }
                          >
                            {passwordStrength < 50 ? "약함" : passwordStrength < 75 ? "보통" : "강함"}
                          </span>
                        </div>
                        <Progress value={passwordStrength} className="h-2" />
                      </div>
                    )}
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="confirmPassword"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>비밀번호 확인</FormLabel>
                    <FormControl>
                      <Input type="password" placeholder="비밀번호 재입력" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="acceptTerms"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-start space-x-3 space-y-0">
                    <FormControl>
                      <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                    </FormControl>
                    <div className="space-y-1 leading-none">
                      <FormLabel className="text-sm">
                        <Link href="/terms" className="text-blue-600 hover:underline">
                          서비스 이용약관
                        </Link>{" "}
                        및{" "}
                        <Link href="/privacy" className="text-blue-600 hover:underline">
                          개인정보 처리방침
                        </Link>
                        에 동의합니다
                      </FormLabel>
                    </div>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <Button type="submit" className="w-full" disabled={isLoading || emailAvailable === false}>
                {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                계정 생성
              </Button>
            </form>
          </Form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              이미 계정이 있으신가요?{" "}
              <Link href="/auth/login" className="text-blue-600 hover:underline">
                로그인
              </Link>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
