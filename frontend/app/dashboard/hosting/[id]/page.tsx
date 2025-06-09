"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Skeleton } from "@/components/ui/skeleton"
import { hostingApi } from "@/lib/hosting"
import { useToast } from "@/hooks/use-toast"
import { ArrowLeft, Copy, ExternalLink, RefreshCw, Terminal, Server, Activity, HardDrive, Cpu } from "lucide-react"
import Link from "next/link"
import { HostingMetrics } from "@/components/dashboard/hosting-metrics"
import { HostingLogs } from "@/components/dashboard/hosting-logs"
import { SSHInfoDialog } from "@/components/dashboard/ssh-info-dialog"
import { Dialog } from "@/components/ui/dialog"
import type { HostingInstance } from "@/types/hosting"

const statusConfig = {
  creating: { label: "Creating", color: "bg-blue-500", icon: RefreshCw },
  running: { label: "Running", color: "bg-green-500", icon: Server },
  stopping: { label: "Stopping", color: "bg-yellow-500", icon: RefreshCw },
  stopped: { label: "Stopped", color: "bg-gray-500", icon: Server },
  error: { label: "Error", color: "bg-red-500", icon: Server },
}

export default function HostingDetailPage() {
  const params = useParams()
  const router = useRouter()
  const { showSuccess, showError } = useToast()
  const [instance, setInstance] = useState<HostingInstance | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [sshDialogOpen, setSshDialogOpen] = useState(false)

  const id = params.id as string

  useEffect(() => {
    fetchInstance()
  }, [id])

  const fetchInstance = async () => {
    setIsLoading(true)
    try {
      const { instance } = await hostingApi.getById(id)
      setInstance(instance)
    } catch (error: any) {
      showError("Failed to load hosting instance")
      router.push("/dashboard/hosting")
    } finally {
      setIsLoading(false)
    }
  }

  const refreshInstance = async () => {
    setIsRefreshing(true)
    try {
      const { instance } = await hostingApi.getById(id)
      setInstance(instance)
      showSuccess("Instance status refreshed")
    } catch (error) {
      showError("Failed to refresh instance status")
    } finally {
      setIsRefreshing(false)
    }
  }

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text)
    showSuccess(`${label} copied to clipboard!`)
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-2">
          <Button variant="outline" size="icon" disabled>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <Skeleton className="h-8 w-48" />
        </div>
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-4 w-32" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-32 w-full" />
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!instance) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-2">
          <Button variant="outline" size="icon" asChild>
            <Link href="/dashboard/hosting">
              <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
          <h1 className="text-2xl font-bold">Instance Not Found</h1>
        </div>
        <Card>
          <CardContent className="pt-6">
            <p>The hosting instance you're looking for doesn't exist or has been deleted.</p>
            <Button asChild className="mt-4">
              <Link href="/dashboard/hosting">Back to Hosting</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  const status = statusConfig[instance.status]
  const StatusIcon = status.icon

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Button variant="outline" size="icon" asChild>
            <Link href="/dashboard/hosting">
              <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
          <h1 className="text-2xl font-bold">VM-{instance.vmId}</h1>
          <Badge variant="secondary" className="flex items-center gap-1">
            <div className={`w-2 h-2 rounded-full ${status.color}`} />
            {status.label}
            {(instance.status === "creating" || instance.status === "stopping") && (
              <StatusIcon className="h-3 w-3 animate-spin ml-1" />
            )}
          </Badge>
        </div>

        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={refreshInstance}
            disabled={isRefreshing}
            className="flex items-center gap-1"
          >
            <RefreshCw className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => window.open(instance.webUrl, "_blank")}
            disabled={instance.status !== "running"}
          >
            <ExternalLink className="mr-2 h-4 w-4" />
            View Site
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setSshDialogOpen(true)}
            disabled={instance.status !== "running"}
          >
            <Terminal className="mr-2 h-4 w-4" />
            SSH Info
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Instance Details</CardTitle>
          <CardDescription>Basic information about your hosting instance</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Web URL</h3>
              <div className="flex items-center gap-2">
                <code className="flex-1 px-3 py-2 bg-gray-100 dark:bg-gray-800 rounded text-sm">{instance.webUrl}</code>
                <Button size="sm" variant="outline" onClick={() => copyToClipboard(instance.webUrl, "Web URL")}>
                  <Copy className="h-4 w-4" />
                </Button>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">SSH Connection</h3>
              <div className="flex items-center gap-2">
                <code className="flex-1 px-3 py-2 bg-gray-100 dark:bg-gray-800 rounded text-sm">
                  {instance.sshInfo.username}@{instance.sshInfo.host}
                </code>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => copyToClipboard(`${instance.sshInfo.username}@${instance.sshInfo.host}`, "SSH Info")}
                >
                  <Copy className="h-4 w-4" />
                </Button>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Created</h3>
              <p>{new Date(instance.createdAt).toLocaleString()}</p>
            </div>

            <div>
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Last Updated</h3>
              <p>{new Date(instance.updatedAt).toLocaleString()}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Resource Usage</CardTitle>
          <CardDescription>Current resource utilization of your instance</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <Cpu className="h-4 w-4 mr-2 text-blue-500" />
                  <span className="text-sm font-medium">CPU Usage</span>
                </div>
                <span className="text-sm font-bold">24%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
                <div className="bg-blue-500 h-2.5 rounded-full" style={{ width: "24%" }}></div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <HardDrive className="h-4 w-4 mr-2 text-green-500" />
                  <span className="text-sm font-medium">Memory Usage</span>
                </div>
                <span className="text-sm font-bold">512MB / 1GB</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
                <div className="bg-green-500 h-2.5 rounded-full" style={{ width: "50%" }}></div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <Activity className="h-4 w-4 mr-2 text-purple-500" />
                  <span className="text-sm font-medium">Disk Usage</span>
                </div>
                <span className="text-sm font-bold">2.4GB / 10GB</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
                <div className="bg-purple-500 h-2.5 rounded-full" style={{ width: "24%" }}></div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="metrics">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="metrics">Performance Metrics</TabsTrigger>
          <TabsTrigger value="logs">Server Logs</TabsTrigger>
        </TabsList>
        <TabsContent value="metrics" className="mt-4">
          <Card>
            <CardContent className="pt-6">
              <HostingMetrics instanceId={id} />
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="logs" className="mt-4">
          <Card>
            <CardContent className="pt-6">
              <HostingLogs instanceId={id} />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* SSH Info Dialog */}
      <Dialog open={sshDialogOpen} onOpenChange={setSshDialogOpen}>
        <SSHInfoDialog instance={instance} />
      </Dialog>
    </div>
  )
}
