import { zodResolver } from "@hookform/resolvers/zod"
import { useQuery } from "@tanstack/react-query"
import { Link, useRouter } from "@tanstack/react-router"
import { AlertCircle, Loader2, Plus, X } from "lucide-react"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Separator } from "@/components/ui/separator"
import { Textarea } from "@/components/ui/textarea"
import { createTeam, listTags } from "@/lib/generated/api"

const createTeamSchema = z.object({
  name: z.string().min(1, "Team name is required"),
  description: z.string().optional(),
})

type CreateTeamFormData = z.infer<typeof createTeamSchema>

export function CreateTeamForm() {
  const router = useRouter()
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [tagInput, setTagInput] = useState("")

  const { data: existingTags = [] } = useQuery({
    queryKey: ["tags"],
    queryFn: async () => {
      const response = await listTags()
      return response.data?.items ?? []
    },
  })

  const form = useForm<CreateTeamFormData>({
    resolver: zodResolver(createTeamSchema),
    defaultValues: {
      name: "",
      description: "",
    },
  })

  const addTag = (tagName: string) => {
    const trimmed = tagName.trim().toLowerCase()
    if (trimmed && !selectedTags.includes(trimmed)) {
      setSelectedTags([...selectedTags, trimmed])
    }
    setTagInput("")
  }

  const removeTag = (tag: string) => {
    setSelectedTags(selectedTags.filter((t) => t !== tag))
  }

  const handleTagKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault()
      addTag(tagInput)
    }
  }

  const onSubmit = async (data: CreateTeamFormData) => {
    try {
      await createTeam({
        body: {
          name: data.name,
          description: data.description,
          tags: selectedTags.length > 0 ? selectedTags : undefined,
        },
      })
      router.invalidate()
      router.navigate({ to: "/teams" })
    } catch (_error) {
      form.setError("root", {
        message: "Failed to create team",
      })
    }
  }

  // Filter suggestions based on input
  const tagSuggestions = existingTags.filter((tag) => tag.name.toLowerCase().includes(tagInput.toLowerCase()) && !selectedTags.includes(tag.name.toLowerCase()))

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Team Name</FormLabel>
              <FormControl>
                <Input placeholder="Engineering" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="description"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Description</FormLabel>
              <FormControl>
                <Textarea placeholder="What does this team do?" className="resize-none" rows={3} {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormItem>
          <FormLabel>Tags</FormLabel>
          <FormDescription className="mb-2">Categorize your team for easier discovery</FormDescription>
          <FormControl>
            <div className="space-y-3">
              <div className="relative">
                <Input
                  placeholder="Type a tag and press Enter..."
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  onKeyDown={handleTagKeyDown}
                  onBlur={() => tagInput && addTag(tagInput)}
                  className="pr-10"
                />
                {tagInput && (
                  <Button type="button" variant="ghost" size="sm" className="absolute top-1/2 right-1 h-7 w-7 -translate-y-1/2 p-0" onClick={() => addTag(tagInput)}>
                    <Plus className="h-4 w-4" />
                    <span className="sr-only">Add tag</span>
                  </Button>
                )}
                {tagInput && tagSuggestions.length > 0 && (
                  <div className="absolute z-10 mt-1 w-full rounded-md border border-border bg-popover p-1 shadow-lg">
                    {tagSuggestions.slice(0, 5).map((tag) => (
                      <button
                        key={tag.id}
                        type="button"
                        className="flex w-full items-center gap-2 rounded px-3 py-2 text-left text-sm hover:bg-accent"
                        onClick={() => addTag(tag.name)}
                      >
                        <span className="text-muted-foreground">#</span>
                        {tag.name}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              {selectedTags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {selectedTags.map((tag) => (
                    <Badge key={tag} variant="secondary" className="gap-1.5 py-1 pr-1 pl-2.5">
                      <span className="text-muted-foreground">#</span>
                      {tag}
                      <button type="button" onClick={() => removeTag(tag)} className="ml-0.5 rounded-full p-0.5 transition-colors hover:bg-muted-foreground/20">
                        <X className="h-3 w-3" />
                        <span className="sr-only">Remove {tag}</span>
                      </button>
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          </FormControl>
        </FormItem>

        {form.formState.errors.root && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{form.formState.errors.root.message}</AlertDescription>
          </Alert>
        )}

        <Separator />

        <div className="flex items-center justify-between">
          <Button type="button" variant="ghost" asChild>
            <Link to="/teams">Cancel</Link>
          </Button>
          <Button type="submit" disabled={form.formState.isSubmitting}>
            {form.formState.isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {form.formState.isSubmitting ? "Creating..." : "Create Team"}
          </Button>
        </div>
      </form>
    </Form>
  )
}
