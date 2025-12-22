import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { createTag, deleteTag, listTags, updateTag, type Tag } from "@/lib/generated/api"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"

export function AdminTags() {
  const queryClient = useQueryClient()
  const [newTagName, setNewTagName] = useState("")
  const [editingTag, setEditingTag] = useState<Tag | null>(null)
  const [editTagName, setEditTagName] = useState("")

  const { data: tags = [], isLoading, isError } = useQuery({
    queryKey: ["admin-tags"],
    queryFn: async () => {
      const response = await listTags()
      return response.data?.items ?? []
    },
  })

  const createTagMutation = useMutation({
    mutationFn: async (name: string) => {
      await createTag({
        body: { name },
        path: { tag_id: crypto.randomUUID() },
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-tags"] })
      setNewTagName("")
    },
  })

  const updateTagMutation = useMutation({
    mutationFn: async ({ tag, name }: { tag: Tag; name: string }) => {
      await updateTag({
        body: { name },
        path: { tag_id: tag.id },
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-tags"] })
      setEditingTag(null)
      setEditTagName("")
    },
  })

  const deleteTagMutation = useMutation({
    mutationFn: async (tag: Tag) => {
      await deleteTag({
        path: { tag_id: tag.id },
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-tags"] })
    },
  })

  if (isLoading) {
    return <div className="text-muted-foreground">Loading tags…</div>
  }

  if (isError) {
    return <div className="text-muted-foreground">We couldn’t load tags yet. Try again shortly.</div>
  }

  const handleCreateTag = (e: React.FormEvent) => {
    e.preventDefault()
    if (newTagName.trim()) {
      createTagMutation.mutate(newTagName.trim())
    }
  }

  const handleUpdateTag = (e: React.FormEvent) => {
    e.preventDefault()
    if (editingTag && editTagName.trim()) {
      updateTagMutation.mutate({ tag: editingTag, name: editTagName.trim() })
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Create New Tag</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleCreateTag} className="flex gap-2">
            <Input value={newTagName} onChange={(e) => setNewTagName(e.target.value)} placeholder="Enter tag name" />
            <Button type="submit">Create</Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Tags</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Slug</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {tags.length === 0 && (
                <TableRow>
                  <TableCell colSpan={3} className="text-center text-muted-foreground">
                    No tags created yet.
                  </TableCell>
                </TableRow>
              )}
              {tags.map((tag) => (
                <TableRow key={tag.id}>
                  <TableCell>
                    {editingTag?.id === tag.id ? (
                      <form onSubmit={handleUpdateTag} className="flex gap-2">
                        <Input value={editTagName} onChange={(e) => setEditTagName(e.target.value)} placeholder="Enter tag name" />
                        <Button type="submit">Save</Button>
                        <Button
                          variant="outline"
                          onClick={() => {
                            setEditingTag(null)
                            setEditTagName("")
                          }}
                        >
                          Cancel
                        </Button>
                      </form>
                    ) : (
                      tag.name
                    )}
                  </TableCell>
                  <TableCell className="text-muted-foreground">{tag.slug}</TableCell>
                  <TableCell>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setEditingTag(tag)
                          setEditTagName(tag.name)
                        }}
                      >
                        Edit
                      </Button>
                      <Button variant="destructive" size="sm" onClick={() => deleteTagMutation.mutate(tag)}>
                        Delete
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
