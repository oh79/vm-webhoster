"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import { useToast } from "@/hooks/use-toast"

interface HostingMetricsProps {
  instanceId: string
}

interface MetricData {
  timestamp: string
  value: number
}

interface ChartData {
  name: string
  value: number
}

export function HostingMetrics({ instanceId }: HostingMetricsProps) {
  const [isLoading, setIsLoading] = useState(true)
  const [timeRange, setTimeRange] = useState("24h")
  const [cpuData, setCpuData] = useState<ChartData[]>([])
  const [memoryData, setMemoryData] = useState<ChartData[]>([])
  const [networkData, setNetworkData] = useState<ChartData[]>([])
  const { showError } = useToast()

  useEffect(() => {
    fetchMetrics()
  }, [instanceId, timeRange])

  const fetchMetrics = async () => {
    setIsLoading(true)
    try {
      // In a real app, this would fetch from your API
      // const response = await api.get(`/hosting/${instanceId}/metrics?timeRange=${timeRange}`)
      // const data = response.data

      // For demo, we'll generate mock data
      const mockData = generateMockData(timeRange)
      setCpuData(mockData.cpu)
      setMemoryData(mockData.memory)
      setNetworkData(mockData.network)
    } catch (error) {
      showError("Failed to load metrics data")
    } finally {
      setIsLoading(false)
    }
  }

  const generateMockData = (range: string): { cpu: ChartData[]; memory: ChartData[]; network: ChartData[] } => {
    const points = range === "24h" ? 24 : range === "7d" ? 7 : 30
    const cpu: ChartData[] = []
    const memory: ChartData[] = []
    const network: ChartData[] = []

    for (let i = 0; i < points; i++) {
      const name = range === "24h" ? `${i}:00` : `Day ${i + 1}`
      cpu.push({
        name,
        value: Math.floor(Math.random() * 60) + 10,
      })
      memory.push({
        name,
        value: Math.floor(Math.random() * 70) + 20,
      })
      network.push({
        name,
        value: Math.floor(Math.random() * 500) + 100,
      })
    }

    return { cpu, memory, network }
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="flex justify-between">
          <Skeleton className="h-10 w-32" />
          <Skeleton className="h-10 w-24" />
        </div>
        <Skeleton className="h-[300px] w-full" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium">Performance Over Time</h3>
        <Select value={timeRange} onValueChange={setTimeRange}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Select time range" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="24h">Last 24 Hours</SelectItem>
            <SelectItem value="7d">Last 7 Days</SelectItem>
            <SelectItem value="30d">Last 30 Days</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Tabs defaultValue="cpu">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="cpu">CPU Usage</TabsTrigger>
          <TabsTrigger value="memory">Memory Usage</TabsTrigger>
          <TabsTrigger value="network">Network Traffic</TabsTrigger>
        </TabsList>
        <TabsContent value="cpu" className="pt-4">
          <Card className="p-4">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={cpuData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis unit="%" />
                <Tooltip formatter={(value) => [`${value}%`, "CPU Usage"]} />
                <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </TabsContent>
        <TabsContent value="memory" className="pt-4">
          <Card className="p-4">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={memoryData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis unit="%" />
                <Tooltip formatter={(value) => [`${value}%`, "Memory Usage"]} />
                <Line type="monotone" dataKey="value" stroke="#10b981" strokeWidth={2} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </TabsContent>
        <TabsContent value="network" className="pt-4">
          <Card className="p-4">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={networkData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis unit="KB/s" />
                <Tooltip formatter={(value) => [`${value} KB/s`, "Network Traffic"]} />
                <Line type="monotone" dataKey="value" stroke="#8b5cf6" strokeWidth={2} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
