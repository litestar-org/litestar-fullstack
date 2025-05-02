import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { TeamMember } from "@/lib/api";
import { getTeam, removeMemberFromTeam } from "@/lib/api/sdk.gen";
import { useAuthStore } from "@/lib/auth";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

interface TeamMembersProps {
  teamId: string;
}

export function TeamMembers({ teamId }: TeamMembersProps) {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();

  const { data: team } = useQuery({
    queryKey: ["team", teamId],
    queryFn: () => getTeam({ path: { team_id: teamId } }),
  });

  const { mutate: removeMember } = useMutation({
    mutationFn: (userId: string) =>
      removeMemberFromTeam({
        path: { team_id: teamId },
        body: { userName: userId },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["team", teamId] });
    },
  });

  if (!team?.data) {
    return null;
  }

  const ownerId = team.data.members?.find((member) => member.isOwner)?.id;
  const canManageMembers = ownerId === user?.id || user?.isSuperuser;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Team Members</h2>
        {canManageMembers && <Button>Add Member</Button>}
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
          {team.data.members?.map((member: TeamMember) => (
            <TableRow key={member.id}>
              <TableCell>{member.name}</TableCell>
              <TableCell>{member.email}</TableCell>
              <TableCell>{member.isOwner ? "Owner" : member.role === "ADMIN" ? "Admin" : "Member"}</TableCell>
              {canManageMembers && !member.isOwner && (
                <TableCell>
                  <Button variant="destructive" size="sm" onClick={() => removeMember(member.id)}>
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
