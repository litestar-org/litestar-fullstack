import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { TeamsService } from '@/lib/api/services/TeamsService';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useAuthStore } from '@/lib/auth';

interface TeamMembersProps {
  teamId: string;
}

export function TeamMembers({ teamId }: TeamMembersProps) {
  const teamsService = new TeamsService();
  const { user } = useAuthStore();
  const queryClient = useQueryClient();

  const { data: team } = useQuery({
    queryKey: ['team', teamId],
    queryFn: () => teamsService.getTeam(teamId),
  });

  const { mutate: removeMember } = useMutation({
    mutationFn: (userId: string) =>
      teamsService.removeTeamMember(teamId, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['team', teamId] });
    },
  });

  if (!team?.data) {
    return null;
  }

  const canManageMembers = team.data.owner_id === user?.id || user?.is_superuser;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Team Members</h2>
        {canManageMembers && (
          <Button>Add Member</Button>
        )}
      </div>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Email</TableHead>
            <TableHead>Role</TableHead>
            {canManageMembers && <TableHead>Actions</TableHead>}
          </TableRow>
        </TableHeader>
        <TableBody>
          {team.data.members?.map((member) => (
            <TableRow key={member.id}>
              <TableCell>{member.name}</TableCell>
              <TableCell>{member.email}</TableCell>
              <TableCell>
                {member.id === team.data.owner_id
                  ? 'Owner'
                  : member.is_superuser
                  ? 'Admin'
                  : 'Member'}
              </TableCell>
              {canManageMembers && member.id !== team.data.owner_id && (
                <TableCell>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => removeMember(member.id)}
                  >
                    Remove
                  </Button>
                </TableCell>
              )}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
