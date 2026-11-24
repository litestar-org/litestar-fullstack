import { useQuery } from "@tanstack/react-query"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { SkeletonTable } from "@/components/ui/skeleton"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { adminListAuditLogsOptions } from "@/lib/generated/api/@tanstack/react-query.gen"

const PAGE_SIZE = 50

export function AuditLogTable() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState("")
  const [action, setAction] = useState("")
  const [endDate, setEndDate] = useState("")

  const { data, isLoading, isError } = useQuery(
    adminListAuditLogsOptions({
      query: {
        currentPage: page,
        pageSize: PAGE_SIZE,
        searchString: search || undefined,
        action: action || undefined,
        end_date: endDate || undefined,
      },
    }),
  )

  if (isLoading) {
    return <SkeletonTable rows={6} />
  }

  if (isError || !data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Audit log</CardTitle>
        </CardHeader>
        <CardContent className="text-muted-foreground">We could not load audit logs.</CardContent>
      </Card>
    )
  }

  const items = data.items ?? []
  const total = data.total ?? 0
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  return (
    <Card>
      <CardHeader>
        <CardTitle>Audit log</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 md:grid-cols-3">
          <Input
            placeholder="Search"
            value={search}
            onChange={(event) => {
              setSearch(event.target.value)
              setPage(1)
            }}
          />
          <Input
            placeholder="Action"
            value={action}
            onChange={(event) => {
              setAction(event.target.value)
              setPage(1)
            }}
          />
          <Input
            placeholder="Created before (ISO)"
            value={endDate}
            onChange={(event) => {
              setEndDate(event.target.value)
              setPage(1)
            }}
          />
        </div>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Action</TableHead>
              <TableHead>Actor</TableHead>
              <TableHead>Target</TableHead>
              <TableHead>Created</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.length === 0 && (
              <TableRow>
                <TableCell colSpan={4} className="text-center text-muted-foreground">
                  No audit entries found.
                </TableCell>
              </TableRow>
            )}
            {items.map((entry) => (
              <TableRow key={entry.id}>
                <TableCell>{entry.action}</TableCell>
                <TableCell className="text-muted-foreground">{entry.actorEmail ?? entry.actorId ?? "System"}</TableCell>
                <TableCell className="text-muted-foreground">{entry.targetLabel ?? entry.targetId ?? "-"}</TableCell>
                <TableCell className="text-muted-foreground">{new Date(entry.createdAt).toLocaleString()}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <div className="flex items-center justify-between">
          <p className="text-xs text-muted-foreground">
            Page {page} of {totalPages}
          </p>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1}>
              Previous
            </Button>
            <Button variant="outline" size="sm" onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page >= totalPages}>
              Next
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
