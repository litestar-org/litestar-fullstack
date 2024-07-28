import * as React from "react"
import {
  PlusCircleIcon,
  CheckIcon,
  ChevronsUpDown,
  CircleCheckBigIcon,
  Check,
  PlusIcon,
} from "lucide-react"
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
import { usePage } from "@inertiajs/react"
import { ComponentPropsWithoutRef, useState } from "react"

type PopoverTriggerProps = ComponentPropsWithoutRef<typeof PopoverTrigger>

interface TeamSwitcherProps extends PopoverTriggerProps {}

export function TeamSwitcher({ className }: TeamSwitcherProps) {
  const { auth, currentTeam } = usePage<InertiaProps>().props
  const [open, setOpen] = useState(false)
  const [showNewTeamDialog, setShowNewTeamDialog] = useState(false)
  const [selectedTeam, setSelectedTeam] = React.useState(currentTeam)

  return (
    <Dialog open={showNewTeamDialog} onOpenChange={setShowNewTeamDialog}>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="ghost"
            size="sm"
            aria-expanded={open}
            aria-label="Select a team"
            className={cn("w-[200px] justify-between opacity-50", className)}
          >
            {selectedTeam?.teamId === currentTeam?.teamId ? (
              <>
                {" "}
                <PlusIcon className="mr-2 h-4 w-4" />
                Select a team
              </>
            ) : (
              <>
                {" "}
                <Avatar className="mr-2 h-5 w-5">
                  <AvatarFallback>
                    {getInitials(selectedTeam?.teamName || "Team")}
                  </AvatarFallback>
                </Avatar>
                {selectedTeam?.teamName}
              </>
            )}
            <ChevronsUpDown className="ml-auto h-4 w-4 shrink-0 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[200px] p-0 focus:outline-none">
          <Command className="rounded-lg border shadow-md">
            {" "}
            <CommandInput placeholder="Search team..." />
            <CommandList>
              <CommandEmpty>No team found.</CommandEmpty>
              <CommandGroup key="teams" heading="Teams">
                {auth?.user?.teams.map((team) => (
                  <CommandItem
                    key={team.teamId}
                    onSelect={(currentValue) => {
                      setSelectedTeam(
                        currentValue === selectedTeam?.teamId ? undefined : team
                      )
                      setOpen(false)
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

              <CommandGroup key="create">
                <DialogTrigger asChild>
                  <CommandItem
                    key="show-create-team"
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
        <DialogHeader>
          <DialogTitle>Create team</DialogTitle>
          <DialogDescription>Add a new team.</DialogDescription>
        </DialogHeader>
        <div>
          <div className="space-y-4 py-2 pb-4">
            <div className="space-y-2">
              <Label htmlFor="name">Team name</Label>
              <Input id="name" placeholder="Acme Inc." />
            </div>
            <div className="space-y-2">
              <Label htmlFor="plan">Description</Label>
              <Input id="description" placeholder="Acme Inc." />
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setShowNewTeamDialog(false)}>
            Cancel
          </Button>
          <Button type="submit">Continue</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
