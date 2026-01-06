import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { Check, ChevronRight, Plus, Search, Shield, Users } from "lucide-react"
import { useEffect, useState } from "react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { useAuthStore } from "@/lib/auth"
import { listTeams, type Team } from "@/lib/generated/api"

function getTeamInitials(name: string): string {
  return name
    .split(/\s+/)
    .map((word) => word[0])
    .join("")
    .toUpperCase()
    .slice(0, 2)
}

function getTeamColor(name: string): string {
  const colors = [
    "bg-blue-500/15 text-blue-600 dark:text-blue-400",
    "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400",
    "bg-violet-500/15 text-violet-600 dark:text-violet-400",
    "bg-amber-500/15 text-amber-600 dark:text-amber-400",
    "bg-rose-500/15 text-rose-600 dark:text-rose-400",
    "bg-cyan-500/15 text-cyan-600 dark:text-cyan-400",
    "bg-fuchsia-500/15 text-fuchsia-600 dark:text-fuchsia-400",
    "bg-orange-500/15 text-orange-600 dark:text-orange-400",
  ]
  const index = name.split("").reduce((acc, char) => acc + char.charCodeAt(0), 0) % colors.length
  return colors[index]
}

export function TeamList() {
  const { user, currentTeam, setCurrentTeam, setTeams } = useAuthStore()
  const [search, setSearch] = useState("")

  const {
    data: teamsData = [],
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["teams"],
    queryFn: async () => {
      const response = await listTeams()
      return response.data?.items ?? []
    },
  })

  useEffect(() => {
    if (!isLoading && !isError) {
      setTeams(teamsData)
    }
  }, [isError, isLoading, setTeams, teamsData])

  const filteredTeams = teamsData.filter((team) => team.name.toLowerCase().includes(search.toLowerCase()) || team.description?.toLowerCase().includes(search.toLowerCase()))

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          <p className="text-sm text-muted-foreground">Loading teams…</p>
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <Card className="border-dashed border-destructive/30 bg-destructive/5">
        <CardContent className="py-12 text-center">
          <p className="text-muted-foreground">We couldn't load teams yet. Try refreshing.</p>
        </CardContent>
      </Card>
    )
  }

  if (teamsData.length === 0) {
    return (
      <Card className="border-dashed border-2">
        <CardContent className="py-16 text-center space-y-6">
          <div className="mx-auto w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
            <Users className="h-8 w-8 text-primary" />
          </div>
          <div className="space-y-2">
            <h3 className="text-lg font-semibold">Create your first team</h3>
            <p className="text-muted-foreground text-sm max-w-md mx-auto">
              Teams help you organize members and control access across the app. Get started by creating your first team.
            </p>
          </div>
          <Button asChild size="lg">
            <Link to="/teams/new">
              <Plus className="mr-2 h-4 w-4" />
              Create team
            </Link>
          </Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {teamsData.length > 3 && (
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input placeholder="Search teams..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-10" />
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {filteredTeams.map((team: Team) => {
          const isActive = currentTeam?.id === team.id
          const tags = team.tags ?? []
          const memberCount = team.members?.length ?? 0
          const userMembership = team.members?.find((m) => m.userId === user?.id)
          const isOwner = userMembership?.isOwner
          const isAdmin = userMembership?.role === "ADMIN"

          return (
            <Card
              key={team.id}
              className={`group relative overflow-hidden transition-all hover:shadow-md ${
                isActive ? "border-primary/50 bg-primary/5 shadow-primary/10 shadow-sm ring-1 ring-primary/20" : "border-border/60 hover:border-border"
              }`}
            >
              {/* Active indicator stripe */}
              {isActive && <div className="absolute inset-y-0 left-0 w-1 bg-primary" />}

              <CardHeader className="pb-3">
                <div className="flex items-start gap-3">
                  <button type="button" onClick={() => setCurrentTeam(team)} className="group/avatar relative" title={isActive ? "Current team" : "Click to switch to this team"}>
                    <Avatar className={`h-12 w-12 transition-all ${getTeamColor(team.name)} ${!isActive && "group-hover/avatar:ring-2 group-hover/avatar:ring-primary/30"}`}>
                      <AvatarFallback className={`text-sm font-semibold ${getTeamColor(team.name)}`}>{getTeamInitials(team.name)}</AvatarFallback>
                    </Avatar>
                    {isActive && (
                      <div className="absolute -bottom-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-primary text-primary-foreground ring-2 ring-background">
                        <Check className="h-3 w-3" />
                      </div>
                    )}
                  </button>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <Link to="/teams/$teamId" params={{ teamId: team.id }} className="font-semibold hover:underline truncate text-foreground">
                        {team.name}
                      </Link>
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-muted-foreground flex items-center gap-1">
                        <Users className="h-3 w-3" />
                        {memberCount} member{memberCount !== 1 ? "s" : ""}
                      </span>
                      {(isOwner || isAdmin) && (
                        <Badge variant="outline" className="h-5 px-1.5 text-[10px] font-medium">
                          {isOwner ? (
                            "Owner"
                          ) : (
                            <>
                              <Shield className="mr-0.5 h-2.5 w-2.5" />
                              Admin
                            </>
                          )}
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              </CardHeader>

              <CardContent className="pt-0">
                {team.description ? (
                  <p className="text-sm text-muted-foreground line-clamp-2 min-h-10">{team.description}</p>
                ) : (
                  <p className="text-sm text-muted-foreground/60 italic min-h-10">No description</p>
                )}

                {tags.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-3">
                    {tags.slice(0, 3).map((tag) => (
                      <Badge key={tag.id} variant="secondary" className="text-[10px] px-2 py-0.5">
                        {tag.name}
                      </Badge>
                    ))}
                    {tags.length > 3 && (
                      <Badge variant="outline" className="text-[10px] px-2 py-0.5">
                        +{tags.length - 3}
                      </Badge>
                    )}
                  </div>
                )}

                <div className="mt-4 pt-3 border-t border-border/60">
                  <Link
                    to="/teams/$teamId"
                    params={{ teamId: team.id }}
                    className="flex items-center justify-between text-sm font-medium text-muted-foreground hover:text-foreground transition-colors group/link"
                  >
                    <span>View team</span>
                    <ChevronRight className="h-4 w-4 transition-transform group-hover/link:translate-x-0.5" />
                  </Link>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {filteredTeams.length === 0 && search && (
        <Card className="border-dashed">
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">No teams match "{search}"</p>
          </CardContent>
        </Card>
      )}

      {filteredTeams.length > 0 && (
        <p className="text-xs text-muted-foreground text-center">
          Showing {filteredTeams.length} of {teamsData.length} team
          {teamsData.length === 1 ? "" : "s"}
        </p>
      )}
    </div>
  )
}
