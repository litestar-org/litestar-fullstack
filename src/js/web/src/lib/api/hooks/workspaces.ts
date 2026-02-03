import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import {
  createTask,
  createWorkspace,
  deleteTask,
  getWorkspace,
  listWorkspaces,
  updateTask,
  type Task,
  type TaskCreate,
  type TaskUpdate,
  type Workspace,
  type WorkspaceCreate,
} from "@/lib/generated/api"

export function useWorkspaces(page = 1, pageSize = 25) {
  return useQuery({
    queryKey: ["workspaces", page, pageSize],
    queryFn: async () => {
      const response = await listWorkspaces({
        query: {
          currentPage: page,
          pageSize,
        },
      })
      return response.data as { items: Workspace[]; total: number }
    },
  })
}

export function useWorkspace(workspaceId: string) {
  return useQuery({
    queryKey: ["workspace", workspaceId],
    queryFn: async () => {
      const response = await getWorkspace({
        path: { workspace_id: workspaceId },
      })
      return response.data as Workspace
    },
    enabled: !!workspaceId,
  })
}

export function useCreateWorkspace() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: WorkspaceCreate) => {
      const response = await createWorkspace({
        body: data,
      })
      return response.data as Workspace
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspaces"] })
      toast.success("Workspace created")
    },
    onError: () => {
      toast.error("Failed to create workspace")
    },
  })
}

export function useCreateTask() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: TaskCreate) => {
      const response = await createTask({
        body: data,
      })
      return response.data as Task
    },
    onSuccess: (data) => {
      if (data?.workspaceId) {
        queryClient.invalidateQueries({ queryKey: ["workspace", data.workspaceId] })
      }
      toast.success("Task created")
    },
    onError: () => {
      toast.error("Failed to create task")
    },
  })
}

export function useUpdateTask(workspaceId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ taskId, data }: { taskId: string; data: TaskUpdate }) => {
      const response = await updateTask({
        path: { task_id: taskId },
        body: data,
      })
      return response.data as Task
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspace", workspaceId] })
      toast.success("Task updated")
    },
    onError: () => {
      toast.error("Failed to update task")
    },
  })
}

export function useDeleteTask(workspaceId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (taskId: string) => {
      await deleteTask({
        path: { task_id: taskId },
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspace", workspaceId] })
      toast.success("Task deleted")
    },
    onError: () => {
      toast.error("Failed to delete task")
    },
  })
}
