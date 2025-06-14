export interface Plan {
  id: string
  name: string
  price: number
  features: string[]
  resources: {
    cpu: number
    memory: number
    storage: number
    bandwidth: number
  }
}

export interface Invoice {
  id: string
  amount: number
  status: "paid" | "pending" | "overdue"
  date: string
  dueDate: string
  items: {
    description: string
    quantity: number
    unitPrice: number
    amount: number
  }[]
}

export interface PaymentMethod {
  id: string
  type: "card" | "paypal"
  last4?: string
  brand?: string
  expiryMonth?: number
  expiryYear?: number
  email?: string
  isDefault: boolean
}
