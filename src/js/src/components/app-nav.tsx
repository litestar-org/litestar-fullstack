import { Button } from "@/components/ui/button";
import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuItem,
	DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { accountLogout, accountProfile } from "@/lib/api/sdk.gen";
import { useTeam } from "@/lib/team-context";
import { useTheme } from "@/lib/theme-context";
import { useQuery } from "@tanstack/react-query";
import { Link, useRouter } from "@tanstack/react-router";
import { Moon, Sun } from "lucide-react";

export function AppNav() {
	const router = useRouter();
	const { currentTeam, setCurrentTeam, teams } = useTeam();
	const { theme, toggleTheme } = useTheme();

	const { data: user } = useQuery({
		queryKey: ["me"],
		queryFn: async () => {
			const response = await accountProfile();
			return response.data;
		},
	});

	const handleLogout = async () => {
		await accountLogout();
		router.invalidate();
	};

	return (
		<nav className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
			<div className="container mx-auto px-4 py-4 flex items-center justify-between">
				<div className="flex items-center gap-4">
					<Link to="/" className="font-bold text-lg">
						App
					</Link>

					{currentTeam && (
						<DropdownMenu>
							<DropdownMenuTrigger asChild>
								<Button variant="outline">{currentTeam.name}</Button>
							</DropdownMenuTrigger>
							<DropdownMenuContent>
								{teams.map((team) => (
									<DropdownMenuItem
										key={team.id}
										onClick={() => setCurrentTeam(team)}
									>
										{team.name}
									</DropdownMenuItem>
								))}
								<DropdownMenuItem asChild>
									<Link to="/teams/new">Create Team</Link>
								</DropdownMenuItem>
							</DropdownMenuContent>
						</DropdownMenu>
					)}
				</div>

				<div className="flex items-center gap-4">
					<Button
						variant="ghost"
						size="icon"
						onClick={toggleTheme}
						className="hover:bg-accent hover:text-accent-foreground"
					>
						{theme === "light" ? (
							<Moon className="h-5 w-5" />
						) : (
							<Sun className="h-5 w-5" />
						)}
					</Button>

					{user && (
						<DropdownMenu>
							<DropdownMenuTrigger asChild>
								<Button variant="outline">{user.email}</Button>
							</DropdownMenuTrigger>
							<DropdownMenuContent>
								<DropdownMenuItem onClick={handleLogout}>
									Logout
								</DropdownMenuItem>
							</DropdownMenuContent>
						</DropdownMenu>
					)}
				</div>
			</div>
		</nav>
	);
}
