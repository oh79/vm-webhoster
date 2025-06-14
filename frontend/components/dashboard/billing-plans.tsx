"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter } from "@/components/ui/card"
import { Check } from "lucide-react"
import { cn } from "@/lib/utils"
import type { Plan } from "@/types/billing"

interface BillingPlansProps {
  plans: Plan[]
  currentPlanId: string
}

export function BillingPlans({ plans, currentPlanId }: BillingPlansProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {plans.map((plan) => {
        const isCurrent = plan.id === currentPlanId
        return (
          <Card
            key={plan.id}
            className={cn("flex flex-col", isCurrent && "border-blue-500 dark:border-blue-500 shadow-md")}
          >
            <CardContent className="pt-6 flex-1">
              <div className="text-center mb-4">
                <h3 className="text-xl font-bold">{plan.name}</h3>
                <div className="mt-2">
                  <span className="text-3xl font-bold">${plan.price}</span>
                  <span className="text-gray-500 dark:text-gray-400">/month</span>
                </div>
              </div>

              <div className="space-y-2 mt-6">
                {plan.features.map((feature, index) => (
                  <div key={index} className="flex items-start gap-2">
                    <Check className="h-4 w-4 text-green-500 mt-0.5" />
                    <span className="text-sm">{feature}</span>
                  </div>
                ))}
              </div>
            </CardContent>
            <CardFooter className="pt-2 pb-6">
              <Button variant={isCurrent ? "outline" : "default"} className="w-full" disabled={isCurrent}>
                {isCurrent ? "Current Plan" : "Upgrade"}
              </Button>
            </CardFooter>
          </Card>
        )
      })}
    </div>
  )
}
