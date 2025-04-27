import { accountProfile } from "@/lib/api/sdk.gen";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuItem,
	DropdownMenuLabel,
	DropdownMenuSeparator,
	DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuthStore } from "@/lib/auth";
import { useTeam } from "@/lib/team-context";
import { useQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import {
	BarChart3,
	Building2,
	Home,
	LogOut,
	Settings,
	Shield,
	User,
} from "lucide-react";

export function Sidebar() {
	const { user } = useAuthStore();
	const { currentTeam, setCurrentTeam, teams } = useTeam();

	const { data: userProfile } = useQuery({
		queryKey: ["me"],
		queryFn: async () => {
			const response = await accountProfile();
			return response.data;
		},
	});

	if (!user) return null;

	return (
		<aside className="w-64 border-r bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
			<div className="flex h-full flex-col">
				{/* User Profile Section */}
				<div className="border-b p-4">
					<DropdownMenu>
						<DropdownMenuTrigger asChild>
							<button className="flex w-full items-center gap-3 rounded-lg p-2 hover:bg-accent">
								<Avatar>
									<AvatarImage src={user.avatarUrl || undefined} alt={user.email} />
									<AvatarFallback>
										<User className="h-5 w-5" />
									</AvatarFallback>
								</Avatar>
								<div className="flex flex-col items-start">
									<span className="text-sm font-medium">{user.name || user.email}</span>
									<span className="text-xs text-muted-foreground">{user.email}</span>
								</div>
							</button>
						</DropdownMenuTrigger>
						<DropdownMenuContent align="start" className="w-56">
							<DropdownMenuLabel>My Account</DropdownMenuLabel>
							<DropdownMenuSeparator />
							<DropdownMenuItem asChild>
								<Link to="/home">Profile</Link>
							</DropdownMenuItem>
							<DropdownMenuItem asChild>
								<Link to="/home">Settings</Link>
							</DropdownMenuItem>
							<DropdownMenuSeparator />
							<DropdownMenuItem onClick={() => useAuthStore.getState().logout()}>
								<LogOut className="mr-2 h-4 w-4" />
								Logout
							</DropdownMenuItem>
						</DropdownMenuContent>
					</DropdownMenu>
				</div>

				{/* Team Picker Section */}
				{teams.length > 0 && (
					<div className="border-b p-4">
						<DropdownMenu>
							<DropdownMenuTrigger asChild>
								<Button variant="outline" className="w-full justify-start">
									<Building2 className="mr-2 h-4 w-4" />
									{currentTeam?.name || "Select Team"}
								</Button>
							</DropdownMenuTrigger>
							<DropdownMenuContent align="start" className="w-56">
								{teams.map((team) => (
									<DropdownMenuItem
										key={team.id}
										onClick={() => setCurrentTeam(team)}
									>
										{team.name}
									</DropdownMenuItem>
								))}
								<DropdownMenuSeparator />
								<DropdownMenuItem asChild>
									<Link to="/teams/new">Create Team</Link>
								</DropdownMenuItem>
							</DropdownMenuContent>
						</DropdownMenu>
					</div>
				)}

				{/* Navigation Links */}
				<nav className="flex-1 space-y-1 p-4">
					<Link
						to="/home"
						className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium hover:bg-accent"
					>
						<Home className="h-4 w-4" />
						Home
					</Link>
					{userProfile?.isSuperuser && (
						<Link
							to="/admin"
							className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium hover:bg-accent"
						>
							<Shield className="h-4 w-4" />
							Admin
						</Link>
					)}
					<Link
						to="/home"
						className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium hover:bg-accent"
					>
						<BarChart3 className="h-4 w-4" />
						Analytics
					</Link>
					<Link
						to="/home"
						className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium hover:bg-accent"
					>
						<Settings className="h-4 w-4" />
						Settings
					</Link>
				</nav>
			</div>
		</aside>
	);
}
