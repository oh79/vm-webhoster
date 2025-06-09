"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Check, CreditCard, FileText, Download } from "lucide-react"
import { BillingPlans } from "@/components/dashboard/billing-plans"
import { PaymentMethods } from "@/components/dashboard/payment-methods"
import { InvoiceHistory } from "@/components/dashboard/invoice-history"
import type { Plan, Invoice, PaymentMethod } from "@/types/billing"

// Mock data for demo
const currentPlan: Plan = {
  id: "standard",
  name: "Standard",
  price: 29.99,
  features: [
    "2 CPU Cores",
    "2GB RAM",
    "50GB SSD Storage",
    "2TB Bandwidth",
    "Free SSL Certificate",
    "Daily Backups",
    "24/7 Support",
  ],
  resources: {
    cpu: 2,
    memory: 2,
    storage: 50,
    bandwidth: 2000,
  },
}

const availablePlans: Plan[] = [
  {
    id: "basic",
    name: "Basic",
    price: 9.99,
    features: [
      "1 CPU Core",
      "1GB RAM",
      "25GB SSD Storage",
      "1TB Bandwidth",
      "Free SSL Certificate",
      "Weekly Backups",
      "Email Support",
    ],
    resources: {
      cpu: 1,
      memory: 1,
      storage: 25,
      bandwidth: 1000,
    },
  },
  currentPlan,
  {
    id: "premium",
    name: "Premium",
    price: 59.99,
    features: [
      "4 CPU Cores",
      "8GB RAM",
      "100GB SSD Storage",
      "5TB Bandwidth",
      "Free SSL Certificate",
      "Daily Backups",
      "Priority 24/7 Support",
      "DDoS Protection",
      "Load Balancing",
    ],
    resources: {
      cpu: 4,
      memory: 8,
      storage: 100,
      bandwidth: 5000,
    },
  },
]

const invoices: Invoice[] = [
  {
    id: "INV-001",
    amount: 29.99,
    status: "paid",
    date: "2023-05-01",
    dueDate: "2023-05-15",
    items: [
      {
        description: "Standard Plan - Monthly",
        quantity: 1,
        unitPrice: 29.99,
        amount: 29.99,
      },
    ],
  },
  {
    id: "INV-002",
    amount: 29.99,
    status: "paid",
    date: "2023-06-01",
    dueDate: "2023-06-15",
    items: [
      {
        description: "Standard Plan - Monthly",
        quantity: 1,
        unitPrice: 29.99,
        amount: 29.99,
      },
    ],
  },
  {
    id: "INV-003",
    amount: 29.99,
    status: "pending",
    date: "2023-07-01",
    dueDate: "2023-07-15",
    items: [
      {
        description: "Standard Plan - Monthly",
        quantity: 1,
        unitPrice: 29.99,
        amount: 29.99,
      },
    ],
  },
]

const paymentMethods: PaymentMethod[] = [
  {
    id: "pm-1",
    type: "card",
    last4: "4242",
    brand: "Visa",
    expiryMonth: 12,
    expiryYear: 2025,
    isDefault: true,
  },
  {
    id: "pm-2",
    type: "paypal",
    email: "user@example.com",
    isDefault: false,
  },
]

export default function BillingPage() {
  const [activeTab, setActiveTab] = useState("overview")

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Billing & Subscription</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Manage your subscription, payment methods, and billing history
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid grid-cols-3 md:w-[400px]">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="payment-methods">Payment Methods</TabsTrigger>
          <TabsTrigger value="invoices">Invoices</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Current Plan */}
          <Card>
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle>Current Plan</CardTitle>
                  <CardDescription>Your current subscription plan and usage</CardDescription>
                </div>
                <Badge variant="outline" className="text-green-600 bg-green-50 dark:bg-green-900/20">
                  Active
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div>
                  <h3 className="text-2xl font-bold">{currentPlan.name} Plan</h3>
                  <p className="text-gray-500 dark:text-gray-400">
                    ${currentPlan.price}/month • Next billing date: August 1, 2023
                  </p>
                </div>
                <Button>Change Plan</Button>
              </div>

              <Separator />

              <div>
                <h4 className="font-medium mb-4">Plan Features</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {currentPlan.features.map((feature, index) => (
                    <div key={index} className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-green-500" />
                      <span className="text-sm">{feature}</span>
                    </div>
                  ))}
                </div>
              </div>

              <Separator />

              <div>
                <h4 className="font-medium mb-4">Resource Usage</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>CPU</span>
                      <span>1.2 / {currentPlan.resources.cpu} Cores</span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
                      <div
                        className="bg-blue-500 h-2.5 rounded-full"
                        style={{ width: `${(1.2 / currentPlan.resources.cpu) * 100}%` }}
                      ></div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Memory</span>
                      <span>1.5 / {currentPlan.resources.memory} GB</span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
                      <div
                        className="bg-green-500 h-2.5 rounded-full"
                        style={{ width: `${(1.5 / currentPlan.resources.memory) * 100}%` }}
                      ></div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Storage</span>
                      <span>12 / {currentPlan.resources.storage} GB</span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
                      <div
                        className="bg-purple-500 h-2.5 rounded-full"
                        style={{ width: `${(12 / currentPlan.resources.storage) * 100}%` }}
                      ></div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Bandwidth</span>
                      <span>450 / {currentPlan.resources.bandwidth} GB</span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
                      <div
                        className="bg-yellow-500 h-2.5 rounded-full"
                        style={{ width: `${(450 / currentPlan.resources.bandwidth) * 100}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Payment Method Summary */}
          <Card>
            <CardHeader>
              <CardTitle>Payment Method</CardTitle>
              <CardDescription>Your default payment method</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-3">
                  <CreditCard className="h-8 w-8 text-gray-400" />
                  <div>
                    <p className="font-medium">
                      {paymentMethods[0].type === "card"
                        ? `${paymentMethods[0].brand} ending in ${paymentMethods[0].last4}`
                        : `PayPal (${paymentMethods[0].email})`}
                    </p>
                    {paymentMethods[0].type === "card" && (
                      <p className="text-sm text-gray-500">
                        Expires {paymentMethods[0].expiryMonth}/{paymentMethods[0].expiryYear}
                      </p>
                    )}
                  </div>
                </div>
                <Button variant="outline" onClick={() => setActiveTab("payment-methods")}>
                  Manage
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Recent Invoices */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Invoices</CardTitle>
              <CardDescription>Your recent billing history</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {invoices.slice(0, 3).map((invoice) => (
                  <div key={invoice.id} className="flex justify-between items-center">
                    <div className="flex items-center gap-3">
                      <FileText className="h-5 w-5 text-gray-400" />
                      <div>
                        <p className="font-medium">Invoice #{invoice.id}</p>
                        <p className="text-sm text-gray-500">{new Date(invoice.date).toLocaleDateString()}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <Badge
                        variant="outline"
                        className={
                          invoice.status === "paid"
                            ? "text-green-600 bg-green-50 dark:bg-green-900/20"
                            : invoice.status === "pending"
                              ? "text-yellow-600 bg-yellow-50 dark:bg-yellow-900/20"
                              : "text-red-600 bg-red-50 dark:bg-red-900/20"
                        }
                      >
                        {invoice.status.charAt(0).toUpperCase() + invoice.status.slice(1)}
                      </Badge>
                      <p className="font-medium">${invoice.amount.toFixed(2)}</p>
                      <Button variant="ghost" size="icon">
                        <Download className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-4">
                <Button variant="outline" className="w-full" onClick={() => setActiveTab("invoices")}>
                  View All Invoices
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="payment-methods">
          <PaymentMethods paymentMethods={paymentMethods} />
        </TabsContent>

        <TabsContent value="invoices">
          <InvoiceHistory invoices={invoices} />
        </TabsContent>
      </Tabs>

      {/* Available Plans */}
      <Card>
        <CardHeader>
          <CardTitle>Available Plans</CardTitle>
          <CardDescription>Compare and upgrade to a different plan</CardDescription>
        </CardHeader>
        <CardContent>
          <BillingPlans plans={availablePlans} currentPlanId={currentPlan.id} />
        </CardContent>
      </Card>
    </div>
  )
}
