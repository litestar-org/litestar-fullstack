import { useQuery } from "@tanstack/react-query"
import { Home, ShieldCheck, Users } from "lucide-react"
import type * as React from "react"
import { useEffect } from "react"
import { NavMain, type NavSection } from "@/components/nav-main"
import { NavTeams } from "@/components/nav-teams"
import { NavUser } from "@/components/nav-user"
import { TeamSwitcher } from "@/components/team-switcher"
import { ThemeToggle } from "@/components/theme-toggle"
import { Sidebar, SidebarContent, SidebarFooter, SidebarHeader, SidebarRail } from "@/components/ui/sidebar"
import { useAuthStore } from "@/lib/auth"
import type { Team } from "@/lib/generated/api"
import { listTeamsOptions } from "@/lib/generated/api/@tanstack/react-query.gen"

const MEMBER_NAV_SECTIONS: NavSection[] = [
  { title: "Home", to: "/home", icon: Home },
  {
    title: "Teams",
    to: "/teams",
    icon: Users,
    subLinks: [
      { title: "All teams", to: "/teams" },
      { title: "Create new", to: "/teams/new" },
    ],
  },
]
const ADMIN_NAV_SECTION: NavSection = { title: "Admin", to: "/admin", icon: ShieldCheck }

function joinTeamIds(teams: Team[]): string {
  return teams.map((team) => team.id).join("|")
}

export function AppSidebar(props: React.ComponentProps<typeof Sidebar>) {
  const { teams, currentTeam, setTeams, setCurrentTeam, user, isAuthenticated } = useAuthStore()

  const {
    data: teamPage,
    isLoading,
    isError,
  } = useQuery({
    ...listTeamsOptions(),
    enabled: isAuthenticated,
  })
  const fetchedTeams = teamPage?.items ?? []

  const fetchedTeamIds = joinTeamIds(fetchedTeams)
  const storedTeamIds = joinTeamIds(teams)

  useEffect(() => {
    if (isLoading || isError || fetchedTeamIds === storedTeamIds) {
      return
    }
    setTeams(fetchedTeams)
  }, [isError, isLoading, setTeams, storedTeamIds, fetchedTeamIds, fetchedTeams])

  const navSections = user?.isSuperuser ? [...MEMBER_NAV_SECTIONS, ADMIN_NAV_SECTION] : MEMBER_NAV_SECTIONS
  const switchableTeams = fetchedTeams.length > 0 ? fetchedTeams : teams

  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <TeamSwitcher teams={switchableTeams} currentTeam={currentTeam} onTeamSelect={setCurrentTeam} />
      </SidebarHeader>
      <SidebarContent>
        <NavMain sections={navSections} />
        {teams.length > 0 && <NavTeams teams={teams} />}
      </SidebarContent>
      <SidebarFooter>
        <div className="flex items-center gap-2">
          <div className="flex-1 min-w-0">
            <NavUser />
          </div>
          <div className="shrink-0 group-data-[collapsible=icon]:hidden">
            <ThemeToggle />
          </div>
        </div>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
