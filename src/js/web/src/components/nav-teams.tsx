import { Link } from "@tanstack/react-router"
import { Users } from "lucide-react"
import { SidebarGroup, SidebarGroupLabel, SidebarMenu, SidebarMenuButton, SidebarMenuItem } from "@/components/ui/sidebar"
import type { Team } from "@/lib/generated/api"

interface NavTeamsProps {
  teams: Team[]
}

export function NavTeams({ teams }: Readonly<NavTeamsProps>) {
  return (
    <SidebarGroup className="group-data-[collapsible=icon]:hidden">
      <SidebarGroupLabel>Teams</SidebarGroupLabel>
      <SidebarMenu>
        {teams.map((team) => (
          <SidebarMenuItem key={team.id}>
            <SidebarMenuButton asChild>
              <Link to="/teams/$teamId" params={{ teamId: team.id }}>
                <Users />
                <span>{team.name}</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        ))}
      </SidebarMenu>
    </SidebarGroup>
  )
}
