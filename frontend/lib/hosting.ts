import api from "./api"
import type { HostingInstance, CreateHostingRequest, HostingResponse } from "@/types/hosting"
import type { StandardResponse } from "@/types/auth"

export const hostingApi = {
  getAll: async (): Promise<StandardResponse<HostingInstance>> => {
    const response = await api.get<StandardResponse<HostingInstance>>("/host/my")
    return response.data
  },

  getById: async (id: string): Promise<StandardResponse<HostingInstance>> => {
    const response = await api.get<StandardResponse<HostingInstance>>(`/host/${id}`)
    return response.data
  },

  create: async (data: CreateHostingRequest): Promise<StandardResponse<HostingInstance>> => {
    const response = await api.post<StandardResponse<HostingInstance>>("/host", data)
    return response.data
  },

  delete: async (): Promise<StandardResponse<any>> => {
    const response = await api.delete<StandardResponse<any>>("/host/my")
    return response.data
  },

  getStatus: async (): Promise<StandardResponse<HostingInstance>> => {
    const response = await api.get<StandardResponse<HostingInstance>>("/host/my")
    return response.data
  },
}
