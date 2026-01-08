import { Link } from "@tanstack/react-router"
import { ChevronsUpDown, Plus, Users } from "lucide-react"
import * as React from "react"

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { SidebarMenu, SidebarMenuButton, SidebarMenuItem, useSidebar } from "@/components/ui/sidebar"
import type { Team } from "@/lib/generated/api"

export function TeamSwitcher({ teams, currentTeam, onTeamSelect }: { teams: Team[]; currentTeam: Team | null; onTeamSelect: (team: Team) => void }) {
  const { isMobile } = useSidebar()
  const activeTeam = React.useMemo(() => {
    if (currentTeam) {
      return teams.find((team) => team.id === currentTeam.id) ?? teams[0]
    }
    return teams[0]
  }, [currentTeam, teams])

  if (!activeTeam) {
    return null
  }

  const initials = activeTeam.name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <SidebarMenuButton size="lg" className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground">
              <div className="flex aspect-square size-8 shrink-0 items-center justify-center rounded-lg bg-sidebar-primary/15 text-sidebar-primary">
                <span className="text-xs font-semibold">{initials}</span>
              </div>
              <div className="grid flex-1 text-left text-sm leading-tight group-data-[collapsible=icon]:hidden">
                <span className="truncate font-medium">{activeTeam.name}</span>
                <span className="truncate text-xs text-muted-foreground">{activeTeam.slug}</span>
              </div>
              <ChevronsUpDown className="ml-auto group-data-[collapsible=icon]:hidden" />
            </SidebarMenuButton>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-(--radix-dropdown-menu-trigger-width) min-w-56 rounded-lg" align="start" side={isMobile ? "bottom" : "right"} sideOffset={4}>
            <DropdownMenuLabel className="text-muted-foreground text-xs">Teams</DropdownMenuLabel>
            {teams.map((team, index) => (
              <DropdownMenuItem key={team.id} onClick={() => onTeamSelect(team)} className="gap-2 p-2">
                <div className="flex size-6 items-center justify-center rounded-md border border-border/60 bg-background">
                  <Users className="size-3.5 shrink-0 text-muted-foreground" />
                </div>
                {team.name}
                <DropdownMenuShortcut>⌘{index + 1}</DropdownMenuShortcut>
              </DropdownMenuItem>
            ))}
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild className="p-2">
              <Link to="/teams/new" className="flex items-center gap-2">
                <div className="flex size-6 items-center justify-center rounded-md border bg-transparent">
                  <Plus className="size-4" />
                </div>
                <span className="font-medium text-muted-foreground">Add team</span>
              </Link>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  )
}
