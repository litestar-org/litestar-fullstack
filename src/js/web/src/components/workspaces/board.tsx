import { Task, TaskStatus } from "@/lib/generated/api"
import { useUpdateTask } from "@/lib/api/hooks/workspaces"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ArrowLeft, ArrowRight } from "lucide-react"

interface BoardProps {
  workspaceId: string
  tasks: Task[]
}

const COLUMNS: { id: TaskStatus; title: string }[] = [
  { id: "todo", title: "To Do" },
  { id: "in-progress", title: "In Progress" },
  { id: "done", title: "Done" },
]

export function KanbanBoard({ workspaceId, tasks }: BoardProps) {
  const updateTask = useUpdateTask(workspaceId)

  const handleStatusChange = (taskId: string, newStatus: TaskStatus) => {
    updateTask.mutate({ taskId, data: { status: newStatus } })
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 h-full">
      {COLUMNS.map((column) => (
        <div key={column.id} className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
             <h3 className="font-semibold text-lg">{column.title}</h3>
             <Badge variant="secondary">
               {tasks.filter(t => t.status === column.id).length}
             </Badge>
          </div>
          <div className="bg-muted/50 p-4 rounded-lg min-h-[500px] flex flex-col gap-3">
            {tasks
              .filter((task) => task.status === column.id)
              .map((task) => (
                <TaskCard 
                  key={task.id} 
                  task={task} 
                  onStatusChange={handleStatusChange} 
                />
              ))}
          </div>
        </div>
      ))}
    </div>
  )
}

function TaskCard({ 
  task, 
  onStatusChange 
}: { 
  task: Task
  onStatusChange: (id: string, status: TaskStatus) => void 
}) {
  return (
    <Card className="cursor-pointer hover:shadow-md transition-shadow">
      <CardHeader className="p-4 pb-2 space-y-0">
        <div className="flex justify-between items-start">
           <CardTitle className="text-sm font-medium leading-none">
             {task.title}
           </CardTitle>
           <PriorityBadge priority={task.priority} />
        </div>
      </CardHeader>
      <CardContent className="p-4 pt-2">
        {task.description && (
          <p className="text-xs text-muted-foreground line-clamp-2 mb-3">
            {task.description}
          </p>
        )}
        <div className="flex gap-2 justify-end mt-2">
           {task.status !== 'todo' && (
             <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => onStatusChange(task.id, task.status === 'done' ? 'in-progress' : 'todo')}>
               <span className="sr-only">Move Back</span>
               <ArrowLeft className="h-4 w-4" />
             </Button>
           )}
           {task.status !== 'done' && (
             <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => onStatusChange(task.id, task.status === 'todo' ? 'in-progress' : 'done')}>
               <span className="sr-only">Move Forward</span>
               <ArrowRight className="h-4 w-4" />
             </Button>
           )}
        </div>
      </CardContent>
    </Card>
  )
}

function PriorityBadge({ priority }: { priority: string }) {
  const colors: Record<string, string> = {
    low: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300",
    medium: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300",
    high: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300",
  }
  return (
    <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${colors[priority] || colors.medium}`}>
      {priority}
    </span>
  )
}
