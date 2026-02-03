import { createFileRoute, Link } from "@tanstack/react-router"
import { useCreateWorkspace, useWorkspaces } from "@/lib/api/hooks/workspaces"
import { Button } from "@/components/ui/button"
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useState } from "react"
import { useAuthStore } from "@/lib/auth"

export const Route = createFileRoute("/_app/workspaces/")({
  component: WorkspacesIndex,
})

function WorkspacesIndex() {
  const { data, isLoading } = useWorkspaces()
  const { currentTeam } = useAuthStore()
  const [open, setOpen] = useState(false)
  
  if (isLoading) return <div>Loading...</div>

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Workspaces</h2>
          <p className="text-muted-foreground">Manage your projects and tasks.</p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button>New Workspace</Button>
          </DialogTrigger>
          <DialogContent>
             <CreateWorkspaceForm onSuccess={() => setOpen(false)} teamId={currentTeam?.id} />
          </DialogContent>
        </Dialog>
      </div>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {data?.items.map((workspace) => (
          <Link 
            key={workspace.id} 
            to="/workspaces/$workspaceId" 
            params={{ workspaceId: workspace.id }}
            className="block"
          >
            <Card className="hover:bg-muted/50 transition-colors h-full">
              <CardHeader>
                <CardTitle>{workspace.name}</CardTitle>
                <CardDescription>{workspace.description || "No description"}</CardDescription>
              </CardHeader>
            </Card>
          </Link>
        ))}
        {data?.items.length === 0 && (
          <div className="col-span-full text-center py-10 text-muted-foreground">
            No workspaces found. Create one to get started.
          </div>
        )}
      </div>
    </div>
  )
}

function CreateWorkspaceForm({ onSuccess, teamId }: { onSuccess: () => void, teamId?: string }) {
  const createWorkspace = useCreateWorkspace()
  const [name, setName] = useState("")
  const [desc, setDesc] = useState("")

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!teamId) return 
    createWorkspace.mutate({ name, description: desc, teamId }, {
      onSuccess: () => onSuccess()
    })
  }

  if (!teamId) return <div>No active team. Please select a team first.</div>

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
       <DialogHeader>
         <DialogTitle>Create Workspace</DialogTitle>
         <DialogDescription>Add a new workspace to your team.</DialogDescription>
       </DialogHeader>
       <div className="space-y-2">
         <Label htmlFor="name">Name</Label>
         <Input id="name" value={name} onChange={e => setName(e.target.value)} required />
       </div>
       <div className="space-y-2">
         <Label htmlFor="desc">Description</Label>
         <Input id="desc" value={desc} onChange={e => setDesc(e.target.value)} />
       </div>
       <DialogFooter>
         <Button type="submit" disabled={createWorkspace.isPending}>
           {createWorkspace.isPending ? "Creating..." : "Create"}
         </Button>
       </DialogFooter>
    </form>
  )
}
