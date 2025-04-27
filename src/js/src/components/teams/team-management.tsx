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
import type { TeamMember } from "@/lib/api";
import { getTeam, listTeams, removeMemberFromTeam } from "@/lib/api/sdk.gen";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "@tanstack/react-router";
import { InviteMemberDialog } from "./invite-member-dialog";

export function TeamManagement() {
	const { teamId } = useParams({ from: "/_app/teams/$teamId" as const });

	const { data: team } = useQuery({
		queryKey: ["team", teamId],
		queryFn: async () => {
			const response = await getTeam({ path: { team_id: teamId } });
			return response.data;
		},
	});

	const { data: members, isLoading } = useQuery({
		queryKey: ["team-members", teamId],
		queryFn: async () => {
			const response = await listTeams({ query: { ids: [teamId] } });
			return response.data?.items?.[0]?.members ?? [];
		},
	});

	if (isLoading || !team) {
		return <div>Loading...</div>;
	}

	const canManageMembers = team.members?.some(
		(member: TeamMember) => member.role === "ADMIN",
	);

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
							{members?.map((member: TeamMember) => (
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
													await removeMemberFromTeam({
														path: { team_id: teamId },
														body: { userName: member.id },
													});
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
