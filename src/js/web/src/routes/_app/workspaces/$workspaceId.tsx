import { createFileRoute } from "@tanstack/react-router"
import { useWorkspace, useCreateTask } from "@/lib/api/hooks/workspaces"
import { KanbanBoard } from "@/components/workspaces/board"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogTrigger, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useState } from "react"
import { TaskPriority } from "@/lib/generated/api"

export const Route = createFileRoute("/_app/workspaces/$workspaceId")({
  component: WorkspaceDetail,
})

function WorkspaceDetail() {
  const { workspaceId } = Route.useParams()
  const { data: workspace, isLoading } = useWorkspace(workspaceId)
  const [open, setOpen] = useState(false)

  if (isLoading) return <div>Loading...</div>
  if (!workspace) return <div>Workspace not found</div>

  return (
    <div className="flex flex-col h-[calc(100vh-10rem)] space-y-4">
      <div className="flex justify-between items-center">
        <div>
           <h2 className="text-3xl font-bold tracking-tight">{workspace.name}</h2>
           <p className="text-muted-foreground">{workspace.description}</p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
           <DialogTrigger asChild>
             <Button>Add Task</Button>
           </DialogTrigger>
           <DialogContent>
             <CreateTaskForm workspaceId={workspaceId} onSuccess={() => setOpen(false)} />
           </DialogContent>
        </Dialog>
      </div>
      
      <div className="flex-1 overflow-x-auto pb-4">
        <KanbanBoard workspaceId={workspaceId} tasks={workspace.tasks || []} />
      </div>
    </div>
  )
}

function CreateTaskForm({ workspaceId, onSuccess }: { workspaceId: string, onSuccess: () => void }) {
  const createTask = useCreateTask()
  const [title, setTitle] = useState("")
  const [priority, setPriority] = useState<TaskPriority>("medium")

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createTask.mutate({ title, workspaceId, priority }, {
      onSuccess: () => onSuccess()
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <DialogHeader>
        <DialogTitle>Add Task</DialogTitle>
      </DialogHeader>
      <div className="space-y-2">
        <Label htmlFor="title">Title</Label>
        <Input id="title" value={title} onChange={e => setTitle(e.target.value)} required />
      </div>
      <div className="space-y-2">
        <Label htmlFor="priority">Priority</Label>
        <Select value={priority} onValueChange={(val) => setPriority(val as TaskPriority)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="low">Low</SelectItem>
            <SelectItem value="medium">Medium</SelectItem>
            <SelectItem value="high">High</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <DialogFooter>
        <Button type="submit" disabled={createTask.isPending}>
          {createTask.isPending ? "Adding..." : "Add Task"}
        </Button>
      </DialogFooter>
    </form>
  )
}
