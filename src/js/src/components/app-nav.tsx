import { Link, useRouter } from "@tanstack/react-router";
import { useTeam } from "@/lib/team-context";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { useQuery } from "@tanstack/react-query";
import { accountProfile, accountLogout } from '@/lib/api/sdk.gen'

export function AppNav() {
  const router = useRouter();
  const { currentTeam, setCurrentTeam, teams } = useTeam();

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
    <nav className="border-b">
      <div className="container mx-auto px-4 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link to="/" className="font-bold">
            App
          </Link>

          {currentTeam && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost">{currentTeam.name}</Button>
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
          {user && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost">{user.email}</Button>
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
