"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Download, FileText, Eye } from "lucide-react"
import { useState } from "react"
import type { Invoice } from "@/types/billing"

interface InvoiceHistoryProps {
  invoices: Invoice[]
}

export function InvoiceHistory({ invoices }: InvoiceHistoryProps) {
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)

  const viewInvoice = (invoice: Invoice) => {
    setSelectedInvoice(invoice)
    setDialogOpen(true)
  }

  const downloadInvoice = (invoice: Invoice) => {
    // In a real app, this would download the invoice PDF
    alert(`Downloading invoice ${invoice.id}`)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "paid":
        return "text-green-600 bg-green-50 dark:bg-green-900/20"
      case "pending":
        return "text-yellow-600 bg-yellow-50 dark:bg-yellow-900/20"
      case "overdue":
        return "text-red-600 bg-red-50 dark:bg-red-900/20"
      default:
        return ""
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Invoice History</CardTitle>
          <CardDescription>View and download your past invoices</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {invoices.map((invoice) => (
              <div
                key={invoice.id}
                className="flex flex-wrap justify-between items-center p-4 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800"
              >
                <div className="flex items-center gap-3">
                  <FileText className="h-8 w-8 text-gray-400" />
                  <div>
                    <p className="font-medium">Invoice #{invoice.id}</p>
                    <p className="text-sm text-gray-500">
                      {new Date(invoice.date).toLocaleDateString()} • ${invoice.amount.toFixed(2)}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3 mt-3 sm:mt-0">
                  <Badge variant="outline" className={getStatusColor(invoice.status)}>
                    {invoice.status.charAt(0).toUpperCase() + invoice.status.slice(1)}
                  </Badge>
                  <div className="flex gap-2">
                    <Button variant="ghost" size="icon" onClick={() => viewInvoice(invoice)}>
                      <Eye className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon" onClick={() => downloadInvoice(invoice)}>
                      <Download className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Invoice #{selectedInvoice?.id}</DialogTitle>
            <DialogDescription>
              Issued on {selectedInvoice && new Date(selectedInvoice.date).toLocaleDateString()}
            </DialogDescription>
          </DialogHeader>

          {selectedInvoice && (
            <div className="space-y-6">
              <div className="flex justify-between">
                <div>
                  <h3 className="font-bold">Web Hosting Service</h3>
                  <p className="text-sm text-gray-500">123 Hosting Street</p>
                  <p className="text-sm text-gray-500">Servertown, ST 12345</p>
                </div>
                <div className="text-right">
                  <h3 className="font-bold">Invoice #{selectedInvoice.id}</h3>
                  <p className="text-sm text-gray-500">Date: {new Date(selectedInvoice.date).toLocaleDateString()}</p>
                  <p className="text-sm text-gray-500">
                    Due Date: {new Date(selectedInvoice.dueDate).toLocaleDateString()}
                  </p>
                </div>
              </div>

              <div className="border-t border-b py-4">
                <h4 className="font-medium mb-2">Bill To:</h4>
                <p>John Doe</p>
                <p className="text-sm text-gray-500">john.doe@example.com</p>
              </div>

              <div>
                <h4 className="font-medium mb-2">Items:</h4>
                <table className="w-full">
                  <thead>
                    <tr className="text-left border-b">
                      <th className="pb-2">Description</th>
                      <th className="pb-2 text-right">Quantity</th>
                      <th className="pb-2 text-right">Unit Price</th>
                      <th className="pb-2 text-right">Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedInvoice.items.map((item, index) => (
                      <tr key={index} className="border-b">
                        <td className="py-2">{item.description}</td>
                        <td className="py-2 text-right">{item.quantity}</td>
                        <td className="py-2 text-right">${item.unitPrice.toFixed(2)}</td>
                        <td className="py-2 text-right">${item.amount.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr>
                      <td colSpan={3} className="pt-4 text-right font-medium">
                        Total:
                      </td>
                      <td className="pt-4 text-right font-bold">${selectedInvoice.amount.toFixed(2)}</td>
                    </tr>
                  </tfoot>
                </table>
              </div>

              <div className="flex justify-end">
                <Button onClick={() => downloadInvoice(selectedInvoice)}>
                  <Download className="h-4 w-4 mr-2" />
                  Download PDF
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
