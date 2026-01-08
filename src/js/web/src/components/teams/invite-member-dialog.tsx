import { zodResolver } from "@hookform/resolvers/zod"
import { useQueryClient } from "@tanstack/react-query"
import { ShieldCheck, User, UserPlus } from "lucide-react"
import { useState } from "react"
import { useForm } from "react-hook-form"
import * as z from "zod"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { createTeamInvitation, type TeamRoles } from "@/lib/generated/api"

const inviteSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  role: z.enum(["MEMBER", "ADMIN"] as const),
})

type InviteFormData = z.infer<typeof inviteSchema>

interface InviteMemberDialogProps {
  teamId: string
}

export function InviteMemberDialog({ teamId }: InviteMemberDialogProps) {
  const [open, setOpen] = useState(false)
  const queryClient = useQueryClient()

  const form = useForm<InviteFormData>({
    resolver: zodResolver(inviteSchema),
    defaultValues: {
      email: "",
      role: "MEMBER",
    },
  })

  const onSubmit = async (data: InviteFormData) => {
    try {
      await createTeamInvitation({
        path: { team_id: teamId },
        body: {
          email: data.email,
          role: data.role as TeamRoles,
        },
      })
      await queryClient.invalidateQueries({
        queryKey: ["team", teamId],
      })
      await queryClient.invalidateQueries({
        queryKey: ["teamInvitations", teamId],
      })
      setOpen(false)
      form.reset()
    } catch (error) {
      console.error("Failed to send invitation:", error)
      form.setError("root", {
        message: "Failed to send invitation. The user may already be invited.",
      })
    }
  }

  const roleOptions = [
    {
      value: "MEMBER" as const,
      label: "Member",
      description: "Can view and collaborate on team content",
      icon: User,
    },
    {
      value: "ADMIN" as const,
      label: "Admin",
      description: "Can invite members and manage team settings",
      icon: ShieldCheck,
    },
  ]

  const selectedRole = roleOptions.find((opt) => opt.value === form.watch("role"))

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm">
          <UserPlus className="mr-2 h-4 w-4" />
          Invite
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Invite Team Member</DialogTitle>
          <DialogDescription>Send an invitation to join this team. They'll receive an email to accept or decline.</DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-5">
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email address</FormLabel>
                  <FormControl>
                    <Input {...field} type="email" placeholder="colleague@company.com" />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="role"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Role</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select a role">
                          {selectedRole && (
                            <span className="flex items-center gap-2">
                              <selectedRole.icon className="h-4 w-4 text-muted-foreground" />
                              {selectedRole.label}
                            </span>
                          )}
                        </SelectValue>
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {roleOptions.map((option) => (
                        <SelectItem key={option.value} value={option.value} className="py-3">
                          <div className="flex items-start gap-3">
                            <option.icon className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                            <div className="flex flex-col">
                              <span className="font-medium">{option.label}</span>
                              <span className="text-xs text-muted-foreground">{option.description}</span>
                            </div>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormDescription>Choose the permissions level for this member.</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            {form.formState.errors.root && (
              <div className="rounded-md bg-destructive/10 border border-destructive/20 p-3">
                <p className="text-destructive text-sm">{form.formState.errors.root.message}</p>
              </div>
            )}
            <div className="flex justify-end gap-3 pt-2">
              <Button type="button" variant="ghost" onClick={() => setOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={form.formState.isSubmitting}>
                {form.formState.isSubmitting ? "Sending..." : "Send Invitation"}
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
