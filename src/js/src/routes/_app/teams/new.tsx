import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { createTeam } from "@/lib/api/sdk.gen"
import { zodResolver } from "@hookform/resolvers/zod"
import { createFileRoute } from "@tanstack/react-router"
import { useRouter } from "@tanstack/react-router"
import { useForm } from "react-hook-form"
import { z } from "zod"

export const Route = createFileRoute("/_app/teams/new")({
  component: NewTeamPage,
})

const createTeamSchema = z.object({
  name: z.string().min(1, "Team name is required"),
  description: z.string().optional(),
})

type CreateTeamFormData = z.infer<typeof createTeamSchema>

export function NewTeamPage() {
  const router = useRouter()
  const form = useForm<CreateTeamFormData>({
    resolver: zodResolver(createTeamSchema),
    defaultValues: {
      name: "",
      description: "",
    },
  })

  const onSubmit = async (data: CreateTeamFormData) => {
    try {
      await createTeam({
        body: { name: data.name, description: data.description },
      })
      router.invalidate()
      router.navigate({ to: "/teams" })
    } catch (error) {
      form.setError("root", {
        message: "Failed to create team",
      })
    }
  }

  return (
    <div className="mt-12 flex w-full justify-center">
      <Card className="h-fit w-full max-w-md">
        <CardHeader>
          <CardTitle>Create Team</CardTitle>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Team Name</FormLabel>
                    <FormControl>
                      <Input {...field} />
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
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              {form.formState.errors.root && <p className="text-destructive text-sm">{form.formState.errors.root.message}</p>}
              <Button type="submit" className="w-full">
                Create Team
              </Button>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  )
}
