import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Ban, RefreshCw } from "lucide-react"
import { useCallback, useState } from "react"
import { toast } from "sonner"
import { AdminNav } from "@/components/admin/admin-nav"
import { QueueActivityMonitor } from "@/components/queues/queue-activity-monitor"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { PageContainer, PageHeader, PageSection } from "@/components/ui/page-layout"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { SkeletonTable } from "@/components/ui/skeleton"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { extractApiErrorMessage } from "@/lib/api-client"
import { adminCancelQueueTaskMutation, adminListQueueTasksOptions, adminListQueueTasksQueryKey } from "@/lib/generated/api/@tanstack/react-query.gen"
import type { QueueTaskEventPayload } from "@/lib/generated/channels"

export const Route = createFileRoute("/_app/admin/queues")({
  component: AdminQueuesPage,
})

const PAGE_LIMIT = 25
const QUEUE_STATUS_OPTIONS = ["pending", "scheduled", "running", "completed", "failed", "cancelled", "expired"] as const
const TERMINAL_STATUSES = new Set(["completed", "succeeded", "failed", "cancelled", "canceled"])
const CANCELLABLE_STATUSES = new Set(["pending", "queued", "scheduled", "running", "in_progress"])

function AdminQueuesPage() {
  const queryClient = useQueryClient()
  const [statusFilter, setStatusFilter] = useState("")
  const [queueFilter, setQueueFilter] = useState("")
  const [taskNameFilter, setTaskNameFilter] = useState("")
  const [offset, setOffset] = useState(0)

  const queryOptions = adminListQueueTasksOptions({
    query: {
      status: statusFilter || undefined,
      queue: queueFilter || undefined,
      task_name: taskNameFilter || undefined,
      limit: PAGE_LIMIT,
      offset,
    },
  })

  const { data, isLoading, isError, isFetching, refetch } = useQuery(queryOptions)

  const cancelTask = useMutation({
    ...adminCancelQueueTaskMutation(),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: adminListQueueTasksQueryKey() })
      toast.success(result.cancelled ? `Cancelled task ${result.taskId}` : `Task ${result.taskId} could not be cancelled`)
    },
    onError: (error) => {
      toast.error("Unable to cancel task", {
        description: extractApiErrorMessage(error, "Try again later"),
      })
    },
  })

  const handleTaskEvent = useCallback(
    (event: QueueTaskEventPayload) => {
      if (TERMINAL_STATUSES.has(event.status.toLowerCase())) {
        void queryClient.invalidateQueries({ queryKey: adminListQueueTasksQueryKey() })
      }
    },
    [queryClient],
  )

  const total = data?.total ?? 0
  const currentPage = Math.floor(offset / PAGE_LIMIT) + 1
  const totalPages = Math.max(1, Math.ceil(total / PAGE_LIMIT))

  return (
    <PageContainer className="flex-1 space-y-8">
      <PageHeader eyebrow="Administration" title="Background Queues" description="Monitor live task activity and inspect or cancel queued tasks." />
      <AdminNav />

      <PageSection>
        <QueueActivityMonitor onTaskEvent={handleTaskEvent} />
      </PageSection>

      <PageSection delay={0.1}>
        <Card>
          <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-2">
            <CardTitle>Queue Tasks</CardTitle>
            <Button type="button" variant="outline" size="sm" onClick={() => void refetch()} disabled={isFetching}>
              <RefreshCw className={`mr-1.5 h-3.5 w-3.5 ${isFetching ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 md:grid-cols-3">
              <Select
                value={statusFilter || "all"}
                onValueChange={(value) => {
                  setStatusFilter(value === "all" ? "" : value)
                  setOffset(0)
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="All statuses" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All statuses</SelectItem>
                  {QUEUE_STATUS_OPTIONS.map((status) => (
                    <SelectItem key={status} value={status} className="capitalize">
                      {status}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Input
                placeholder="Filter by queue (e.g. default, emails)"
                value={queueFilter}
                onChange={(event) => {
                  setQueueFilter(event.target.value)
                  setOffset(0)
                }}
              />
              <Input
                placeholder="Filter by task name"
                value={taskNameFilter}
                onChange={(event) => {
                  setTaskNameFilter(event.target.value)
                  setOffset(0)
                }}
              />
            </div>

            {isLoading ? (
              <SkeletonTable rows={6} />
            ) : isError || !data ? (
              <p className="text-sm text-muted-foreground">We could not load queue tasks.</p>
            ) : (
              <>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Task</TableHead>
                      <TableHead>Queue</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Retries</TableHead>
                      <TableHead>Created</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.items.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={6} className="text-center text-muted-foreground">
                          No queue tasks found.
                        </TableCell>
                      </TableRow>
                    )}
                    {data.items.map((task) => {
                      const canCancel = CANCELLABLE_STATUSES.has(task.status.toLowerCase())
                      return (
                        <TableRow key={task.taskId}>
                          <TableCell>
                            <div className="font-medium">{task.taskName}</div>
                            <div className="font-mono text-xs text-muted-foreground">{task.taskId}</div>
                            {task.error && <div className="text-xs text-destructive">{task.error}</div>}
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline">{task.queue}</Badge>
                          </TableCell>
                          <TableCell>
                            <Badge variant="secondary" className="capitalize">
                              {task.status}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            {task.retryCount ?? 0} / {task.maxRetries ?? 0}
                          </TableCell>
                          <TableCell className="text-muted-foreground">{task.createdAt ? new Date(task.createdAt).toLocaleString() : "—"}</TableCell>
                          <TableCell className="text-right">
                            {canCancel && (
                              <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                disabled={cancelTask.isPending}
                                onClick={() => cancelTask.mutate({ path: { task_id: task.taskId } })}
                              >
                                <Ban className="mr-1.5 h-3.5 w-3.5" />
                                Cancel
                              </Button>
                            )}
                          </TableCell>
                        </TableRow>
                      )
                    })}
                  </TableBody>
                </Table>

                <div className="flex items-center justify-between">
                  <p className="text-xs text-muted-foreground">
                    Page {currentPage} of {totalPages} ({total} total)
                  </p>
                  <div className="flex gap-2">
                    <Button type="button" variant="outline" size="sm" onClick={() => setOffset((prev) => Math.max(0, prev - PAGE_LIMIT))} disabled={offset <= 0}>
                      Previous
                    </Button>
                    <Button type="button" variant="outline" size="sm" onClick={() => setOffset((prev) => prev + PAGE_LIMIT)} disabled={offset + PAGE_LIMIT >= total}>
                      Next
                    </Button>
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </PageSection>
    </PageContainer>
  )
}
