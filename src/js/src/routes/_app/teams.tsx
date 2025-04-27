import { createFileRoute } from '@tanstack/react-router'
import { useAuthStore } from '@/lib/auth'
import { Button } from '@/components/ui/button'
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export const Route = createFileRoute('/_app/teams')({
  component: TeamsComponent,
})

function TeamsComponent() {
  const { currentTeam, setCurrentTeam, teams, setTeams } = useAuthStore()
  const queryClient = useQueryClient()

  const { data: teamsData = [], isLoading } = useQuery({
    queryKey: ["teams"],
    queryFn: async () => {
      const response = await api.teams.list()
      return response.data
    },
  })

  const createTeamMutation = useMutation({
    mutationFn: async () => {
      const response = await api.teams.create({
        data: {
          name: "New Team",
          slug: "new-team",
        },
      })
      return response.data
    },
    onSuccess: (newTeam) => {
      setTeams([...teams, newTeam])
      setCurrentTeam(newTeam)
      queryClient.invalidateQueries({ queryKey: ["teams"] })
    },
  })

  if (isLoading) {
    return <div>Loading...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Teams</h1>
        <Button onClick={() => createTeamMutation.mutate()}>Create Team</Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {teamsData.map((team) => (
          <div
            key={team.id}
            className={`rounded-lg border p-4 ${
              currentTeam?.id === team.id
                ? 'border-primary bg-primary/5'
                : 'hover:border-primary/50'
            }`}
            onClick={() => setCurrentTeam(team)}
          >
            <h2 className="text-xl font-semibold">{team.name}</h2>
            <p className="text-sm text-muted-foreground">{team.slug}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

export default TeamsComponent
