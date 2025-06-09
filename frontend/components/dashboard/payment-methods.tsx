"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { CreditCard, Trash2, Plus } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import type { PaymentMethod } from "@/types/billing"

type PaymentMethodsProps = {
  paymentMethods: PaymentMethod[]
}

const cardSchema = z.object({
  cardNumber: z.string().min(16, "Card number must be at least 16 digits"),
  cardholderName: z.string().min(1, "Cardholder name is required"),
  expiryMonth: z.string().min(1, "Expiry month is required"),
  expiryYear: z.string().min(1, "Expiry year is required"),
  cvv: z.string().min(3, "CVV must be at least 3 digits"),
})

type CardForm = z.infer<typeof cardSchema>

export function PaymentMethods({ paymentMethods }: PaymentMethodsProps) {
  const [methods, setMethods] = useState(paymentMethods)
  const [dialogOpen, setDialogOpen] = useState(false)
  const { showSuccess, showError } = useToast()

  const form = useForm<CardForm>({
    resolver: zodResolver(cardSchema),
    defaultValues: {
      cardNumber: "",
      cardholderName: "",
      expiryMonth: "",
      expiryYear: "",
      cvv: "",
    },
  })

  const onSubmit = (data: CardForm) => {
    // In a real app, this would call an API to add the card
    const newMethod: PaymentMethod = {
      id: `pm-${Date.now()}`,
      type: "card",
      last4: data.cardNumber.slice(-4),
      brand: getCardBrand(data.cardNumber),
      expiryMonth: Number.parseInt(data.expiryMonth),
      expiryYear: Number.parseInt(data.expiryYear),
      isDefault: methods.length === 0,
    }

    setMethods([...methods, newMethod])
    setDialogOpen(false)
    form.reset()
    showSuccess("Payment method added successfully")
  }

  const getCardBrand = (cardNumber: string): string => {
    // Simple card brand detection based on first digit
    const firstDigit = cardNumber.charAt(0)
    if (firstDigit === "4") return "Visa"
    if (firstDigit === "5") return "Mastercard"
    if (firstDigit === "3") return "Amex"
    if (firstDigit === "6") return "Discover"
    return "Card"
  }

  const setDefaultMethod = (id: string) => {
    setMethods(
      methods.map((method) => ({
        ...method,
        isDefault: method.id === id,
      })),
    )
    showSuccess("Default payment method updated")
  }

  const removeMethod = (id: string) => {
    const methodToRemove = methods.find((m) => m.id === id)
    if (methodToRemove?.isDefault && methods.length > 1) {
      showError("Cannot remove default payment method. Please set another method as default first.")
      return
    }
    setMethods(methods.filter((method) => method.id !== id))
    showSuccess("Payment method removed")
  }

  const PaypalIconComponent = () => (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="lucide lucide-paypal"
    >
      <path d="M7 11.5V4a1 1 0 0 1 1-1h8a1 1 0 0 1 1 1v3.5" />
      <path d="M17 8h2.3a1 1 0 0 1 .7 1.7L12 16a1 1 0 0 1-1.7-.7V8.7a1 1 0 0 1 1.7-.7L17 12V8Z" />
      <path d="M6.5 10H5a1 1 0 0 0-1 1v7a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1v-3.5" />
      <path d="M18 15h1a1 1 0 0 0 1-1V8a1 1 0 0 0-1-1h-4" />
    </svg>
  )

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Payment Methods</CardTitle>
          <CardDescription>Manage your payment methods</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {methods.map((method) => (
            <div
              key={method.id}
              className="flex justify-between items-center p-4 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800"
            >
              <div className="flex items-center gap-3">
                {method.type === "card" ? <CreditCard className="h-8 w-8 text-gray-400" /> : <PaypalIconComponent />}
                <div>
                  <div className="flex items-center gap-2">
                    <p className="font-medium">
                      {method.type === "card"
                        ? `${method.brand} ending in ${method.last4}`
                        : `PayPal (${method.email})`}
                    </p>
                    {method.isDefault && (
                      <Badge variant="outline" className="text-green-600 bg-green-50 dark:bg-green-900/20">
                        Default
                      </Badge>
                    )}
                  </div>
                  {method.type === "card" && (
                    <p className="text-sm text-gray-500">
                      Expires {method.expiryMonth}/{method.expiryYear}
                    </p>
                  )}
                </div>
              </div>
              <div className="flex gap-2">
                {!method.isDefault && (
                  <Button variant="outline" size="sm" onClick={() => setDefaultMethod(method.id)}>
                    Set Default
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="icon"
                  className="text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
                  onClick={() => removeMethod(method.id)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}

          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button className="w-full">
                <Plus className="h-4 w-4 mr-2" />
                Add Payment Method
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add Payment Method</DialogTitle>
                <DialogDescription>Add a new credit or debit card</DialogDescription>
              </DialogHeader>
              <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                  <FormField
                    control={form.control}
                    name="cardNumber"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Card Number</FormLabel>
                        <FormControl>
                          <Input placeholder="1234 5678 9012 3456" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="cardholderName"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Cardholder Name</FormLabel>
                        <FormControl>
                          <Input placeholder="John Doe" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <div className="grid grid-cols-3 gap-4">
                    <FormField
                      control={form.control}
                      name="expiryMonth"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Month</FormLabel>
                          <Select onValueChange={field.onChange} defaultValue={field.value}>
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue placeholder="MM" />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              {Array.from({ length: 12 }, (_, i) => {
                                const month = i + 1
                                return (
                                  <SelectItem key={month} value={month.toString().padStart(2, "0")}>
                                    {month.toString().padStart(2, "0")}
                                  </SelectItem>
                                )
                              })}
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="expiryYear"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Year</FormLabel>
                          <Select onValueChange={field.onChange} defaultValue={field.value}>
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue placeholder="YY" />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              {Array.from({ length: 10 }, (_, i) => {
                                const year = new Date().getFullYear() + i
                                return (
                                  <SelectItem key={year} value={year.toString()}>
                                    {year}
                                  </SelectItem>
                                )
                              })}
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="cvv"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>CVV</FormLabel>
                          <FormControl>
                            <Input placeholder="123" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  <div className="flex justify-end gap-2 pt-4">
                    <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                      Cancel
                    </Button>
                    <Button type="submit">Add Card</Button>
                  </div>
                </form>
              </Form>
            </DialogContent>
          </Dialog>
        </CardContent>
      </Card>
    </div>
  )
}
