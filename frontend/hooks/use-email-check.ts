"use client"

import { useState, useEffect } from "react"
import { useDebounce } from "./use-debounce"
import api from "@/lib/api"
import * as z from "zod"

export function useEmailCheck(email: string) {
  const [emailAvailable, setEmailAvailable] = useState<boolean | null>(null)
  const [checkingEmail, setCheckingEmail] = useState(false)
  const debouncedEmail = useDebounce(email, 500)

  useEffect(() => {
    const checkEmailAvailability = async () => {
      if (debouncedEmail && z.string().email().safeParse(debouncedEmail).success) {
        setCheckingEmail(true)
        try {
          await api.get(`/auth/check-email?email=${debouncedEmail}`)
          setEmailAvailable(true)
        } catch (error: any) {
          if (error.response?.status === 409) {
            setEmailAvailable(false)
          }
        } finally {
          setCheckingEmail(false)
        }
      } else {
        setEmailAvailable(null)
      }
    }

    checkEmailAvailability()
  }, [debouncedEmail])

  return { emailAvailable, checkingEmail }
}
