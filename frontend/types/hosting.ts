export interface HostingInstance {
  id: number
  user_id: number
  name: string
  vm_id: string
  vm_ip: string
  ssh_port: number
  status: "creating" | "running" | "stopping" | "stopped" | "error"
  created_at: string
  updated_at: string
  web_url?: string
  ssh_command?: string
}

export interface HostingDetail extends HostingInstance {
  user: {
    id: number
    email: string
    username: string
    is_active: boolean
    created_at: string
  }
  web_url: string
  ssh_command: string
}

export type CreateHostingRequest = Record<string, never> // 빈 객체

export interface HostingResponse {
  success: boolean
  message: string
  data: HostingInstance
}

export interface HostingStats {
  total_hostings: number
  active_hostings: number
  creating_hostings: number
  error_hostings: number
}

export interface HostingOperation {
  operation: "start" | "stop" | "restart" | "delete"
}
