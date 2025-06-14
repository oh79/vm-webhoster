"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useToast } from "@/hooks/use-toast"
import { RefreshCw, Download } from "lucide-react"

interface HostingLogsProps {
  instanceId: string
}

interface LogEntry {
  timestamp: string
  level: "info" | "warn" | "error"
  message: string
}

export function HostingLogs({ instanceId }: HostingLogsProps) {
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [logType, setLogType] = useState("application")
  const [logs, setLogs] = useState<LogEntry[]>([])
  const { showError } = useToast()

  useEffect(() => {
    fetchLogs()
  }, [instanceId, logType])

  const fetchLogs = async () => {
    setIsLoading(true)
    try {
      // In a real app, this would fetch from your API
      // const response = await api.get(`/hosting/${instanceId}/logs?type=${logType}`)
      // const data = response.data.logs

      // For demo, we'll generate mock logs
      const mockLogs = generateMockLogs(logType)
      setLogs(mockLogs)
    } catch (error) {
      showError("Failed to load server logs")
    } finally {
      setIsLoading(false)
    }
  }

  const refreshLogs = async () => {
    setIsRefreshing(true)
    try {
      const mockLogs = generateMockLogs(logType)
      setLogs(mockLogs)
    } catch (error) {
      showError("Failed to refresh logs")
    } finally {
      setIsRefreshing(false)
    }
  }

  const downloadLogs = () => {
    const logText = logs.map((log) => `[${log.timestamp}] [${log.level.toUpperCase()}] ${log.message}`).join("\n")
    const blob = new Blob([logText], { type: "text/plain" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `vm-${instanceId}-${logType}-logs.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const generateMockLogs = (type: string): LogEntry[] => {
    const now = new Date()
    const logs: LogEntry[] = []

    const appLogs = [
      { level: "info", message: "Application started successfully" },
      { level: "info", message: "Connected to database" },
      { level: "info", message: "User authentication successful" },
      { level: "warn", message: "High memory usage detected" },
      { level: "error", message: "Failed to connect to external API" },
      { level: "info", message: "Cache cleared successfully" },
      { level: "warn", message: "Slow database query detected" },
      { level: "info", message: "Background job completed" },
      { level: "error", message: "Uncaught exception in worker thread" },
      { level: "info", message: "Config reloaded" },
    ]

    const systemLogs = [
      { level: "info", message: "System boot completed" },
      { level: "info", message: "Service nginx started" },
      { level: "info", message: "Disk space check passed" },
      { level: "warn", message: "High CPU load detected" },
      { level: "error", message: "Failed to mount network drive" },
      { level: "info", message: "Scheduled backup completed" },
      { level: "warn", message: "Swap usage high" },
      { level: "info", message: "Security updates installed" },
      { level: "error", message: "Kernel panic detected" },
      { level: "info", message: "System time synchronized" },
    ]

    const accessLogs = [
      { level: "info", message: '192.168.1.1 - - [GET] "/api/users" 200' },
      { level: "info", message: '192.168.1.2 - - [POST] "/api/login" 200' },
      { level: "warn", message: '192.168.1.3 - - [GET] "/admin" 403' },
      { level: "info", message: '192.168.1.4 - - [GET] "/assets/main.css" 200' },
      { level: "error", message: '192.168.1.5 - - [GET] "/api/products" 500' },
      { level: "info", message: '192.168.1.6 - - [PUT] "/api/users/1" 200' },
      { level: "warn", message: '192.168.1.7 - - [POST] "/api/register" 429' },
      { level: "info", message: '192.168.1.8 - - [GET] "/favicon.ico" 200' },
      { level: "error", message: '192.168.1.9 - - [DELETE] "/api/posts/5" 404' },
      { level: "info", message: '192.168.1.10 - - [GET] "/api/status" 200' },
    ]

    const sourceData = type === "application" ? appLogs : type === "system" ? systemLogs : accessLogs

    for (let i = 0; i < 20; i++) {
      const randomLog = sourceData[Math.floor(Math.random() * sourceData.length)]
      const timestamp = new Date(now.getTime() - i * 60000).toISOString()
      logs.push({
        timestamp,
        level: randomLog.level as "info" | "warn" | "error",
        message: randomLog.message,
      })
    }

    return logs.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
  }

  const getLevelColor = (level: string) => {
    switch (level) {
      case "info":
        return "text-blue-500"
      case "warn":
        return "text-yellow-500"
      case "error":
        return "text-red-500"
      default:
        return "text-gray-500"
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="flex justify-between">
          <Skeleton className="h-10 w-32" />
          <Skeleton className="h-10 w-24" />
        </div>
        <Skeleton className="h-[400px] w-full" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <Select value={logType} onValueChange={setLogType}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Select log type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="application">Application Logs</SelectItem>
            <SelectItem value="system">System Logs</SelectItem>
            <SelectItem value="access">Access Logs</SelectItem>
          </SelectContent>
        </Select>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={refreshLogs} disabled={isRefreshing}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button variant="outline" size="sm" onClick={downloadLogs}>
            <Download className="h-4 w-4 mr-2" />
            Download
          </Button>
        </div>
      </div>

      <div className="border rounded-md overflow-hidden">
        <div className="bg-gray-100 dark:bg-gray-800 p-2 border-b">
          <div className="grid grid-cols-12 gap-4 text-sm font-medium">
            <div className="col-span-3">Timestamp</div>
            <div className="col-span-1">Level</div>
            <div className="col-span-8">Message</div>
          </div>
        </div>
        <div className="max-h-[400px] overflow-y-auto">
          {logs.map((log, index) => (
            <div
              key={index}
              className="grid grid-cols-12 gap-4 p-2 text-sm border-b last:border-0 hover:bg-gray-50 dark:hover:bg-gray-800"
            >
              <div className="col-span-3 font-mono text-gray-500">{new Date(log.timestamp).toLocaleString()}</div>
              <div className={`col-span-1 font-medium ${getLevelColor(log.level)}`}>{log.level.toUpperCase()}</div>
              <div className="col-span-8 font-mono">{log.message}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
