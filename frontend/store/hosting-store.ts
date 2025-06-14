import { create } from "zustand"
import type { HostingInstance } from "@/types/hosting"

interface HostingState {
  instances: HostingInstance[]
  isLoading: boolean
  error: string | null
  setInstances: (instances: HostingInstance[]) => void
  addInstance: (instance: HostingInstance) => void
  updateInstance: (id: string, updates: Partial<HostingInstance>) => void
  removeInstance: (id: string) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
}

export const useHostingStore = create<HostingState>((set) => ({
  instances: [],
  isLoading: false,
  error: null,
  setInstances: (instances) => set({ instances }),
  addInstance: (instance) => set((state) => ({ instances: [...state.instances, instance] })),
  updateInstance: (id, updates) =>
    set((state) => ({
      instances: state.instances.map((instance) => (instance.id === id ? { ...instance, ...updates } : instance)),
    })),
  removeInstance: (id) => set((state) => ({ instances: state.instances.filter((instance) => instance.id !== id) })),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
}))
