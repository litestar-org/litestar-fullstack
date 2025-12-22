import { Home, ShieldCheck, Users } from "lucide-react"
import type * as React from "react"
import { useEffect, useMemo } from "react"

import { NavMain } from "@/components/nav-main"
import { NavProjects } from "@/components/nav-projects"
import { NavUser } from "@/components/nav-user"
import { TeamSwitcher } from "@/components/team-switcher"
import { Sidebar, SidebarContent, SidebarFooter, SidebarHeader, SidebarRail } from "@/components/ui/sidebar"
import { listTeams, type Team } from "@/lib/generated/api"
import { useAuthStore } from "@/lib/auth"
import { useQuery } from "@tanstack/react-query"

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const { teams, currentTeam, setTeams, setCurrentTeam, user, isAuthenticated } = useAuthStore()

  const { data: teamsData = [], isLoading, isError } = useQuery({
    queryKey: ["teams"],
    queryFn: async () => {
      const response = await listTeams()
      return response.data?.items ?? []
    },
    enabled: isAuthenticated,
  })

  const teamIds = useMemo(() => teamsData.map((team) => team.id).join("|"), [teamsData])
  const storeIds = useMemo(() => teams.map((team) => team.id).join("|"), [teams])

  useEffect(() => {
    if (isLoading || isError || teamIds === storeIds) {
      return
    }
    setTeams(teamsData)
  }, [isError, isLoading, setTeams, storeIds, teamIds, teamsData])

  const navMain = useMemo(() => {
    const items = [
      {
        title: "Home",
        to: "/home",
        icon: Home,
      },
      {
        title: "Teams",
        to: "/teams",
        icon: Users,
        items: [
          { title: "All teams", to: "/teams" },
          { title: "Create new", to: "/teams/new" },
        ],
      },
    ]

    if (user?.isSuperuser) {
      items.push({
        title: "Admin",
        to: "/admin",
        icon: ShieldCheck,
      })
    }

    return items
  }, [user?.isSuperuser])

  const teamLinks = useMemo(
    () =>
      teams.map((team: Team) => ({
        name: team.name,
        to: "/teams/$teamId",
        params: { teamId: team.id },
        icon: Users,
      })),
    [teams],
  )
  const teamOptions = teamsData.length > 0 ? teamsData : teams

  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <TeamSwitcher teams={teamOptions} currentTeam={currentTeam} onTeamSelect={setCurrentTeam} />
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={navMain} />
        {teamLinks.length > 0 && <NavProjects label="Teams" projects={teamLinks} />}
      </SidebarContent>
      <SidebarFooter>
        <NavUser />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
