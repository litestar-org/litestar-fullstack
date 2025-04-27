import { useParams } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { InviteMemberDialog } from "./invite-member-dialog";

interface TeamMember {
  id: string;
  name: string;
  email: string;
  role: string;
}

interface Team {
  id: string;
  permissions: string[];
}

export function TeamManagement() {
  const { teamId } = useParams({ from: "/teams/$teamId" });

  const { data: team } = useQuery<Team>({
    queryKey: ["team", teamId],
    queryFn: async () => {
      const response = await api.teams.get(teamId);
      return response.data;
    },
  });

  const { data: members, isLoading } = useQuery<TeamMember[]>({
    queryKey: ["team-members", teamId],
    queryFn: async () => {
      const response = await api.teams.members.list(teamId);
      return response.data;
    },
  });

  if (isLoading || !team) {
    return <div>Loading...</div>;
  }

  const canManageMembers = team.permissions.includes("manage_members");

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Team Members</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex justify-end mb-4">
            {canManageMembers && <InviteMemberDialog teamId={teamId} />}
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
              {members?.map((member) => (
                <TableRow key={member.id}>
                  <TableCell>{member.name}</TableCell>
                  <TableCell>{member.email}</TableCell>
                  <TableCell>{member.role}</TableCell>
                  {canManageMembers && (
                    <TableCell>
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={async () => {
                          await api.teams.members.remove(teamId, member.id);
                        }}
                      >
                        Remove
                      </Button>
                    </TableCell>
                  )}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
