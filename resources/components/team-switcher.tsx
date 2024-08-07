import * as React from "react"
import { PlusCircleIcon, ChevronsUpDown, Check, PlusIcon } from "lucide-react"
import { cn, getInitials } from "@/lib/utils"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { router, usePage } from "@inertiajs/react"
import { ComponentPropsWithoutRef, useState } from "react"
import { CurrentTeam } from "@/types"
import { Head, Link, useForm } from "@inertiajs/react"
import { InputError } from "./input-error"
import { toast } from "./ui/use-toast"
type PopoverTriggerProps = ComponentPropsWithoutRef<typeof PopoverTrigger>

interface TeamSwitcherProps extends PopoverTriggerProps {}

export function TeamSwitcher({ className }: TeamSwitcherProps) {
  const { auth, currentTeam } = usePage<InertiaProps>().props
  const [open, setOpen] = useState(false)
  const [showNewTeamDialog, setShowNewTeamDialog] = useState(false)
  const { data, setData, post, reset, errors, processing } = useForm({
    name: "",
    description: "",
  })

  const createTeam = (e: { preventDefault: () => void }) => {
    e.preventDefault()
    post(route("teams.add"), {
      preserveScroll: true,
      onSuccess: () => {
        reset()
        setShowNewTeamDialog(false)
        toast({
          title: "Team Created",
          description: "Your new team has been created.",
        })
      },
    })
  }
  async function showTeam(teamId: string) {
    try {
      setOpen(false)
      router.get(route("teams.show", teamId))
    } catch (error: any) {
      console.log(error)
    }
  }
  return (
    <Dialog open={showNewTeamDialog} onOpenChange={setShowNewTeamDialog} modal>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="ghost"
            size="sm"
            role="combobox"
            aria-expanded={open}
            aria-label="Select a team"
            className={cn("w-[200px] justify-between opacity-50", className)}
          >
            {currentTeam === undefined ? (
              <>
                <PlusIcon className="mr-2 h-4 w-4" />
                Select a team
              </>
            ) : (
              <>
                <Avatar className="mr-2 h-5 w-5">
                  <AvatarFallback>
                    {getInitials(currentTeam.teamName || "Team")}
                  </AvatarFallback>
                </Avatar>
                {currentTeam.teamName}
              </>
            )}
            <ChevronsUpDown className="ml-auto h-4 w-4 shrink-0 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[200px] p-0 ">
          <Command className="rounded-lg border shadow-md ">
            <CommandInput
              className="border-none focus:ring-transparent"
              placeholder="Search team..."
            />

            <CommandEmpty>No team found.</CommandEmpty>
            <CommandList>
              <CommandGroup key="teams" heading="Teams">
                {auth?.user?.teams.map((team) => (
                  <CommandItem
                    key={team.teamId}
                    value={team.teamName}
                    onSelect={() => {
                      showTeam(team.teamId)
                      setOpen(false)
                      console.log("click")
                    }}
                    className="text-sm"
                  >
                    <Avatar className="mr-2 h-5 w-5">
                      <AvatarFallback>
                        {getInitials(team.teamName)}
                      </AvatarFallback>
                    </Avatar>
                    {team.teamName}
                    <Check
                      className={cn(
                        "ml-auto h-4 w-",
                        currentTeam?.teamId === team.teamId
                          ? "opacity-100 border-lime-700 stroke-lime-500"
                          : "opacity-0"
                      )}
                    />
                  </CommandItem>
                ))}
              </CommandGroup>
              <CommandSeparator />

              <CommandGroup heading="Commands">
                <DialogTrigger asChild>
                  <CommandItem
                    onSelect={() => {
                      setOpen(false)
                      setShowNewTeamDialog(true)
                    }}
                  >
                    <PlusCircleIcon className="mr-2 h-5 w-5" />
                    Create Team
                  </CommandItem>
                </DialogTrigger>
              </CommandGroup>
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
      <DialogContent>
        {" "}
        <form onSubmit={createTeam} className="space-y-6">
          <DialogHeader>
            <DialogTitle>Create team</DialogTitle>
            <DialogDescription>Add a new team.</DialogDescription>
          </DialogHeader>
          <div>
            <div className="space-y-4 py-2 pb-4">
              <div className="space-y-2">
                <Label htmlFor="name">Team name</Label>
                <Input
                  id="name"
                  value={data.name}
                  placeholder="Name your new team"
                  className="mt-1"
                  onChange={(e) => setData("name", e.target.value)}
                  required
                  autoFocus
                  autoComplete="name"
                />
                <InputError className="mt-2" message={errors.name} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Input
                  id="description"
                  value={data.description}
                  placeholder="Tell us a little about this team"
                  onChange={(e) => setData("description", e.target.value)}
                />
                <InputError className="mt-2" message={errors.description} />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowNewTeamDialog(false)
                reset()
              }}
            >
              Cancel
            </Button>
            <Button disabled={processing} type="submit">
              Continue
            </Button>
          </DialogFooter>{" "}
        </form>
      </DialogContent>
    </Dialog>
  )
}
